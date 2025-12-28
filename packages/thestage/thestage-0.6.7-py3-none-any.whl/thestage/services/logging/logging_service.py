import asyncio
from _signal import SIGINT
from asyncio import CancelledError, Task, StreamWriter
from datetime import datetime
from typing import Optional, Dict

import aioconsole
import typer
from httpx import ReadTimeout, ConnectError, ConnectTimeout

from thestage.helpers.logger.app_logger import app_logger
from thestage.services.clients.thestage_api.dtos.enums.container_status import DockerContainerStatus
from thestage.services.clients.thestage_api.dtos.enums.inference_simulator_status import InferenceSimulatorStatus
from thestage.services.clients.thestage_api.dtos.enums.task_status import TaskStatus
from thestage.services.clients.thestage_api.dtos.inference_controller.get_inference_simulator_response import \
    GetInferenceSimulatorResponse
from thestage.services.clients.thestage_api.dtos.task_controller.task_view_response import TaskViewResponse
from thestage.services.logging.byte_print_style import BytePrintStyle
from thestage.services.logging.dto.log_message import LogMessage
from thestage.services.logging.dto.log_type import LogType
from thestage.i18n.translation import __
from thestage.services.abstract_service import AbstractService
from thestage.services.clients.thestage_api.dtos.container_response import DockerContainerDto
from thestage.helpers.error_handler import error_handler
from thestage.services.clients.thestage_api.api_client import TheStageApiClient
from rich import print

from thestage.services.logging.exception.log_polling_exception import LogPollingException
from thestage.services.logging.logging_constants import LOG_MESSAGE_CODE_TASK_FINISHED, \
    LOG_MESSAGE_CODE_INFERENCE_SIMULATOR_FAILED

is_logs_streaming = False


class LoggingService:
    __thestage_api_client: TheStageApiClient = None

    def __init__(
            self,
            thestage_api_client: TheStageApiClient,
    ):
        self.__thestage_api_client = thestage_api_client


    @error_handler()
    def print_last_task_logs(self, task_public_id: str, logs_number: Optional[int]):
        logs = self.__thestage_api_client.query_user_logs(
            task_public_id=task_public_id,
            limit=logs_number
        )
        for log_message in reversed(logs.queryResult):
            self.__print_log_line_object(log_message)


    @error_handler()
    def print_last_inference_simulator_logs(self, inference_simulator_public_id: str, logs_number: Optional[int]):
        logs = self.__thestage_api_client.query_user_logs(
            inference_simulator_public_id=inference_simulator_public_id,
            limit=logs_number
        )
        for log_message in reversed(logs.queryResult):
            self.__print_log_line_object(log_message)


    @error_handler()
    def print_last_container_logs(self, container_public_id: Optional[str], container_slug: Optional[str], logs_number: Optional[int]):
        container: Optional[DockerContainerDto] = self.__thestage_api_client.get_container(
            container_public_id=container_public_id,
            container_slug=container_slug,
        )

        if not container:
            typer.echo("Container was not found")
            raise typer.Exit(1)

        logs = self.__thestage_api_client.query_user_logs(
            container_public_id=container.public_id,
            limit=logs_number
        )
        for log_message in reversed(logs.queryResult):
            self.__print_log_line_object(log_message)


    @error_handler()
    def stream_task_logs_with_controls(self, task_public_id: str):
        asyncio.run(
            self.__stream_task_logs_with_controls_async(task_public_id=task_public_id)
        )


    @error_handler()
    async def __stream_task_logs_with_controls_async(self, task_public_id: str):
        task_view_response: Optional[TaskViewResponse] = self.__thestage_api_client.get_task(task_public_id=task_public_id,)

        task_status_map: Dict[str, str] = self.__thestage_api_client.get_task_localized_status_map()

        task = task_view_response.task

        if task:
            if task.frontend_status.status_key not in [TaskStatus.RUNNING, TaskStatus.SCHEDULED]:
                typer.echo(__("Task must be in status '%required_status%' to stream real-time logs. Task %task_id% status: '%status%'.", {
                    'task_id': str(task.public_id),
                    'status': task.frontend_status.status_translation,
                    'required_status': task_status_map.get(TaskStatus.RUNNING) or TaskStatus.RUNNING
                }))
                raise typer.Exit(1)
        else:
            typer.echo(f"Task with ID {task_public_id} was not found")
            raise typer.Exit(1)

        typer.echo(f"Log stream for task {task.public_id} started")

        typer.echo(__("CTRL+C to cancel the task. CTRL+D to disconnect from log stream."))

        print_logs_task = asyncio.create_task(self.print_realtime_logs(task_public_id=task.public_id))
        input_task = asyncio.create_task(self.read_log_stream_input())

        def sigint_handler():
            input_task.cancel()

        loop = asyncio.get_event_loop()
        for signal_item in [SIGINT]:  # SIGINT == CTRL+C
            loop.add_signal_handler(signal_item, sigint_handler)

        done, pending = await asyncio.wait([print_logs_task, input_task], return_when=asyncio.FIRST_COMPLETED)

        if input_task in done:
            print_logs_task.cancel()
            if not input_task.result():  # result is only expected if ctrl+D triggered EOFError
                typer.echo(f"\rTask {task_public_id} will be canceled")
                self.__thestage_api_client.cancel_task(
                    task_public_id=task.public_id,
                )

    @error_handler()
    def stream_inference_simulator_logs_with_controls(self, public_id: Optional[str] = None, slug: Optional[str] = None):
        asyncio.run(
            self.__stream_inference_simulator_logs_with_controls_async(
                public_id=public_id,
                slug=slug
            )
        )

    @error_handler()
    async def __stream_inference_simulator_logs_with_controls_async(self,  public_id: Optional[str], slug: Optional[str]):
        get_inference_simulator_response: Optional[GetInferenceSimulatorResponse] = self.__thestage_api_client.get_inference_simulator(
            public_id=public_id,
            slug=slug,
        )

        inference_simulator_status_map: Dict[str, str] = self.__thestage_api_client.get_inference_simulator_business_status_map()

        inference_simulator = get_inference_simulator_response.inferenceSimulator

        if inference_simulator:
            if inference_simulator.status not in ['SCHEDULED', 'CREATING', 'RUNNING']:
                typer.echo(
                    __("Inference simulator must be in status '%required_status%' to stream real-time logs. Inference simulator status: '%status%'.",
                       {
                           'status': inference_simulator.status,
                           'required_status': inference_simulator_status_map.get(InferenceSimulatorStatus.RUNNING) or InferenceSimulatorStatus.RUNNING
                       }))
                raise typer.Exit(1)
        else:
            typer.echo("Inference simulator was not found")
            raise typer.Exit(1)

        typer.echo(f"Log stream for inference simulator '{inference_simulator.public_id}' started")

        typer.echo(__("CTRL+D to disconnect from log stream."))

        print_task_or_inference_simulator_logs = asyncio.create_task(
            self.print_realtime_logs(inference_simulator_public_id=inference_simulator.public_id)
        )
        input_task = asyncio.create_task(self.read_log_stream_input())

        done, pending = await asyncio.wait([print_task_or_inference_simulator_logs, input_task],
                                           return_when=asyncio.FIRST_COMPLETED)

        if input_task in done:
            print_task_or_inference_simulator_logs.cancel()
            inference_logs_cmd_id = f"-isn {slug}" if slug else f"-isid {public_id}"
            typer.echo(f"Disconnected from log stream. You can try to reconnect with 'thestage project inference-simulator logs {inference_logs_cmd_id}'")


    @error_handler()
    def stream_container_logs_with_controls(self, container_public_id: Optional[str], container_slug: Optional[str]):
        asyncio.run(
            self.__stream_container_logs_with_controls_async(
                container_public_id=container_public_id,
                container_slug=container_slug
            )
        )


    @error_handler()
    async def __stream_container_logs_with_controls_async(self, container_public_id: Optional[str], container_slug: Optional[str]):
        container: Optional[DockerContainerDto] = self.__thestage_api_client.get_container(
            container_public_id=container_public_id,
            container_slug=container_slug,
        )

        if container:
            if container.frontend_status.status_key not in [DockerContainerStatus.RUNNING]:
                typer.echo(f"Container status: '{container.frontend_status.status_translation}'")
        else:
            typer.echo("Container was not found")
            raise typer.Exit(1)

        typer.echo(f"Log stream for Docker container started")
        typer.echo("CTRL+D to disconnect from log stream.")

        print_logs_task = asyncio.create_task(self.print_realtime_logs(docker_container_public_id=container.public_id))
        input_task = asyncio.create_task(self.read_log_stream_input())

        def sigint_handler():
            input_task.cancel()

        loop = asyncio.get_event_loop()
        for signal_item in [SIGINT]:  # SIGINT == CTRL+C
            loop.add_signal_handler(signal_item, sigint_handler)

        done, pending = await asyncio.wait([print_logs_task, input_task], return_when=asyncio.FIRST_COMPLETED)

        if input_task in done:
            print_logs_task.cancel()


    async def read_log_stream_input(self):
        try:
            while True:
                input1 = await aioconsole.ainput()
        except EOFError:
            typer.echo(__("\rExited from log stream"))
            return True
        except CancelledError:  # Always appears if async task is canceled and leaves huge traces
            pass


    async def print_realtime_logs(
            self,
            task_public_id: Optional[str] = None,
            inference_simulator_public_id: Optional[str] = None,
            docker_container_public_id: Optional[str] = None,
    ):
        polling_interval_seconds: float = 4  # also adjust polling api method timeout if changed
        between_logs_sleeping_coef: float = 1  # we emulate delay between logs, but if for any reason code runs for too long - delays will be controlled with this coef
        last_iteration_log_timestamp: Optional[str] = None  # pointer to next iteration polling start (obtained from each response)
        last_log_id: Optional[str] = None  # pointer to next iteration polling start - to exclude the log id from result (obtained from each response)
        consecutive_error_count: int = 0  # connectivity errors count - stream will disconnect if too many errors in a row
        iteration_started_at: datetime  # used to control iteration duration - polling should be done at around exact rate
        errors_started_at: Optional[datetime] = None  # time since errors started to stream disconnect

        is_no_more_logs = False
        while not is_no_more_logs:
            log_wait_remaining_limit: float = polling_interval_seconds  # hard limit just in case
            iteration_started_at = datetime.utcnow()
            last_printed_log_timestamp: Optional[datetime] = None
            reader, writer = await aioconsole.get_standard_streams()

            # this shows (somewhat accurate) time difference between logs here and in real time. should not grow.
            # if last_iteration_log_timestamp:
            #     last_log_timestamp_parsed = datetime.strptime(last_iteration_log_timestamp, '%Y-%m-%dT%H:%M:%S.%f')
            #     stream_to_logs_diff = datetime.utcnow() - last_log_timestamp_parsed
            #     print_nonblocking(f'TDIFF {stream_to_logs_diff.total_seconds()}', writer)
            try:
                logs_response = await self.__thestage_api_client.poll_logs_httpx(
                    task_public_id=task_public_id,
                    inference_simulator_public_id=inference_simulator_public_id,
                    docker_container_public_id=docker_container_public_id,
                    last_log_timestamp=last_iteration_log_timestamp,
                    last_log_id=last_log_id
                )

                if not logs_response.is_success:
                    app_logger.info(f'Polling logs error: {logs_response.message}')
                    raise LogPollingException('')


                if consecutive_error_count > 0:
                    consecutive_error_count = 0
                    errors_started_at = None
                    log_wait_remaining_limit = 0   # no log delays after reconnect
                    print_nonblocking("Reconnected to log stream", writer, BytePrintStyle.GREEN)

                last_iteration_log_timestamp = logs_response.lastLogTimestamp
                last_log_id = logs_response.lastLogId

                for log_item in logs_response.logs:
                    current_log_timestamp = datetime.strptime(log_item.timestamp[:26], '%Y-%m-%dT%H:%M:%S.%f')  # python does not like nanoseconds
                    if last_printed_log_timestamp is not None and log_wait_remaining_limit > 0:
                        logs_sleeptime = (current_log_timestamp - last_printed_log_timestamp).total_seconds() * between_logs_sleeping_coef
                        await asyncio.sleep(logs_sleeptime)
                        log_wait_remaining_limit -= logs_sleeptime
                    self.__print_log_line_object_nonblocking(log_item, writer)
                    last_printed_log_timestamp = current_log_timestamp
                    if log_item.messageCode == LOG_MESSAGE_CODE_TASK_FINISHED or log_item.messageCode == LOG_MESSAGE_CODE_INFERENCE_SIMULATOR_FAILED:
                        is_no_more_logs = True

                if is_no_more_logs:
                    break
            except (ReadTimeout, ConnectError, ConnectTimeout, LogPollingException) as e:
                consecutive_error_count += 1
                if consecutive_error_count == 1:
                    if isinstance(e, LogPollingException):
                        print_nonblocking("Some problems raised while getting logs...", writer, BytePrintStyle.ORANGE)
                    else:
                        print_nonblocking("Network issues, attempting to re-establish connection...", writer, BytePrintStyle.ORANGE)
                if not errors_started_at:
                    errors_started_at = datetime.utcnow()

            if consecutive_error_count > 7:
                seconds_with_error = (datetime.utcnow() - errors_started_at).total_seconds()
                if inference_simulator_public_id:
                    print_nonblocking(f"Log stream: disconnected from server (connectivity issues for {seconds_with_error} seconds). Try 'thestage inference-simulator logs <inference-simulator-UID>' to reconnect.", writer)
                elif task_public_id:
                    print_nonblocking(f"Log stream: disconnected from server (connectivity issues for {seconds_with_error} seconds). Try 'thestage project task logs {task_public_id}' to reconnect.", writer)
                elif docker_container_public_id:
                    print_nonblocking(f"Log stream: disconnected from server (connectivity issues for {seconds_with_error} seconds). Try 'thestage container logs <docker-container-UID>' to reconnect.", writer)
                else:
                    print_nonblocking(f"Log stream: disconnected from server (connectivity issues for {seconds_with_error} seconds)", writer)
                break

            # depending on iteration duration - sleep for the remaining time and adjust log sleep coefficient if needed
            iteration_duration = (datetime.utcnow() - iteration_started_at).total_seconds()
            if iteration_duration > polling_interval_seconds:
                between_logs_sleeping_coef *= 0.85
            else:
                await asyncio.sleep(polling_interval_seconds - iteration_duration)
                if between_logs_sleeping_coef < 1:
                    between_logs_sleeping_coef = min(1.0, between_logs_sleeping_coef * 1.15)


    def __print_log_line(self, log_message_raw_json: str):
        log_message = LogMessage.model_validate_json(log_message_raw_json)
        if not log_message.logType and log_message.message == 'ping':
            return
        self.__print_log_line_object(log_message)


    @staticmethod
    def __print_log_line_object(log_message: LogMessage):
        line_color: str = "grey78"

        if not log_message.logType and log_message.message == 'ping':
            return

        if log_message.logType == LogType.STDERR.value:
            line_color = "red"
        if log_message.message:
            print(f'[{line_color}][not bold]{log_message.message}[/not bold][/{line_color}]')

    @staticmethod
    def __print_log_line_object_nonblocking(log_message: LogMessage, writer: StreamWriter):
        if log_message.message:
            line_color: str = BytePrintStyle.RESET
            if log_message.logType == LogType.STDERR.value:
                line_color = BytePrintStyle.RED

            print_nonblocking(f'{log_message.message}', writer, line_color)


def print_nonblocking(line: str, writer: StreamWriter, color_code: str = BytePrintStyle.RESET):
    writer.write(str.encode(f'{color_code}{line}{BytePrintStyle.RESET}\r\n'))
