# Introduction

[TheStage AI](https://app.thestage.ai/) is an integrated platform designed for AI researchers, focusing on solving challenges related to accelerating deep neural network (DNN) inference.

**TheStage CLI** provides a command-line interface for interacting with TheStage AI infrastructure, allowing researchers to:

- **Server Instances:** Retrieve information and connect to instances.
- **Docker Containers:** Manage containers by retrieving information, connecting, streaming real-time logs, uploading/downloading files, and starting/stopping containers.
- **Projects:** Clone and initialize projects, retrieve project specific task information, run tasks within a project, and stream real-time task logs.

TheStage AI's web-based interface provides full control over managing resources such as creating, renting, deleting components, etc..

# Requirements

TheStage CLI is developed using Python and Poetry. Supported versions are Python 3.9 to 3.12 and Poetry 1.7.1. While the CLI is compatible with various operating systems, we recommend using a Unix-like OS such as Linux or macOS for optimal performance.

**Additional Software Requirements:**

- Git
- Python 3.9 to 3.12
- SSH client

These tools must be installed for the CLI to function correctly.

# Authentication and Authorization

To securely connect to TheStage AI's backend and access information about server instances, containers, and more, API tokens are required. These tokens serve as both authentication and authorization mechanisms and can be generated through TheStage AI's web application.

**Note:** An account on TheStage AI is required to generate an API token. Please refer to TheStage AI documentation: TheStage AI Platform: [SSH Keys and API Tokens](https://docs.thestage.ai/platform/build/thestage-ai-ssh-keys-and-api-tokens.html) for more information.

# Installation and Initialization

To generate an API token, please login to your [TheStage AI account](https://app.thestage.ai/sign-in),  and navigate to the Profile > API tokens section. Please refer to [TheStage AI platform documentation](https://docs.thestage.ai/platform/build/thestage-ai-ssh-keys-and-api-tokens.html) for more information.

```python
# To install TheStage CLI:
pip install thestage

# To upgrade thestage CLI:
pip install thestage --upgrade

# To set or change an API token:
thestage config set --api-token <API_token>

# To get help:
thestage --help
```

# Using the CLI

## **Unique IDs**

When working with components of your computational cluster—such as server instances, Docker containers, and projects—the CLI often requires you to specify the unique ID of the component. This unique ID is assigned when the component is created in TheStage AI web application and can be found in your TheStage AI account or by listing the components using the CLI.

## **Connecting to server instances and containers**

When connecting to a **rented server instance** or a Docker container hosted on it, the CLI uses the SSH key assigned to that server instance, which is stored in TheStage AI platform. If the instance status is "online" but the connection cannot be established, verify that an SSH key is associated with the server instance. For more information, see [your TheStage AI account > Profile > SSH Keys](https://app.thestage.ai/profile/ssh).

When connecting to a **self-hosted instance** or a Docker container running on it, the CLI requires the username to be specified because it does not have information on which user to use. Ensure that the specified user has SSH access to the server. The instance status must be "online" for a successful connection. For more information, see [TheStage AI Platform: Self-hosted Instances](https://docs.thestage.ai/platform/build/thestage-ai-self-hosted-instances.html).

# Additional Resources

For comprehensive documentation on TheStage AI platform, please visit [TheStage AI Platform Documentation](https://docs.thestage.ai/platform/build/README.html).

For more in-depth information on using TheStage CLI, including command references, please refer to [TheStage AI Platform: CLI](https://docs.thestage.ai/platform/build/thestage-ai-cli.html).

# License

TheStage CLI is licensed under the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0) (the "License"). You may not use TheStage CLI except in compliance with the License. Unless required by applicable law or agreed to in writing, software distributed under the License is provided on an "as-is" basis, without warranties or conditions of any kind, either express or implied.