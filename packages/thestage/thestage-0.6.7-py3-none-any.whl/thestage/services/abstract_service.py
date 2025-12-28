from abc import ABC
from typing import List, Dict, Any, Optional

import typer
from tabulate import tabulate
from thestage.i18n.translation import __
from thestage.services.abstract_mapper import AbstractMapper
from thestage.services.clients.thestage_api.dtos.paginated_entity_list import PaginatedEntityList


class AbstractService(ABC):
    # TODO remove recursion
    def print(
            self,
            func_get_data,
            func_special_params: Dict[str, Any],
            mapper: AbstractMapper,
            headers: List[str],
            row: int = 5,
            page: int = 1,
            show_index: str = 'always',
            max_col_width: List[Optional[int]] = None,
            depth: int = 0,
    ):
        paginated_entity_list: PaginatedEntityList = func_get_data(
            row=row,
            page=page,
            **func_special_params,
        )

        result = list(map(lambda x: mapper.build_entity(x), paginated_entity_list.entities))

        if result:
            raw_data = [list(item.model_dump(
                by_alias=True,
            ).values()) for item in result]
        else:
            if depth == 0:
                typer.echo(__("No items found"))
            else:
                typer.echo(__("Listing completed"))
            raise typer.Exit(0)

        # tabulate() crashes on any None value, check mappers

        typer.echo(__(
            "Current page: %page% | Total pages: %total_pages% | Items per page: %limit%",
            {
                'page': str(page),
                'limit': str(row),
                'total_pages': str(paginated_entity_list.pagination_data.total_pages),
            }
        ))

        typer.echo(tabulate(
            raw_data,
            headers=headers,
            showindex=show_index,
            tablefmt="double_grid",
            maxcolwidths=max_col_width,
        ))

        if page >= paginated_entity_list.pagination_data.total_pages:
            typer.echo(__("Listing completed"))
            raise typer.Exit(0)

        next_page: int = typer.prompt(
            text=__('Go to next page (0 to exit)?'),
            default=page + 1,
            show_choices=False,
            type=int,
            show_default=True,
        )
        if next_page == 0:
            raise typer.Exit(0)
        else:
            self.print(
                func_get_data=func_get_data,
                func_special_params=func_special_params,
                mapper=mapper,
                headers=headers,
                row=row,
                page=next_page,
                max_col_width=max_col_width,
                show_index=show_index,
                depth=depth + 1,
            )
