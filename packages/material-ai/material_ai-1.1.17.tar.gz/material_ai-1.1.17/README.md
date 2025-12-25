# Material AI
*You build the agents. We'll handle the rest.*

## Material-AI Project Generator 🚀

To create a new project, open your terminal, and run the command below. This will download the interactive setup script, make it executable, and then launch it.

[//]: # ( x-release-please-start-version )

```bash
wget https://raw.githubusercontent.com/muralimanoharv/material-ai/refs/tags/v1.1.17/scripts/create_project.sh && \
chmod +x ./create_project.sh && \
./create_project.sh && \
rm ./create_project.sh
```
[//]: # (x-release-please-end)
-----
Follow the on-screen prompts to generate your new project directory.



## Current Challenges with the Agent Development Kit (ADK)

While the Google Agent Development Kit (ADK) is a powerful tool for rapidly building and prototyping conversational agents, several challenges emerge when transitioning from a development environment to a live, production-grade application for enterprise customers. These challenges include:

1.  **Enterprise Authentication:** Standard ADK deployments lack a straightforward way to integrate with diverse customer SSO (Single Sign-On) systems, making secure, enterprise-wide adoption difficult.
2.  **A Production-Ready User Interface:** The default web UI is designed primarily for testing and development. It is not intended for a polished, customer-facing experience and lacks the rich design and features that end-users expect from a modern application.
3.  **Bespoke Custom Functionality:** Implementing custom business logic—such as systems to capture LLM feedback, integrate with internal enterprise APIs, or fetch user-specific data—requires significant effort outside the core ADK framework.
4.  **Robust Session Management & Authorization:** The ADK does not provide built-in, enterprise-grade mechanisms for managing user sessions or defining granular, role-based authorization rules. These are critical for security, control, and personalization in any multi-user environment.

## Introducing Material AI: The Solution

**Material AI** is a comprehensive framework built to solve these exact challenges. It enhances the ADK by providing the necessary layers for security, user experience, and custom functionality, turning your agent prototypes into secure, scalable, and enterprise-ready AI applications.

### Focus on What Matters: Building Great Agents

Material AI is designed for a **streamlined developer experience**. The framework is incredibly easy to set up and handles all the difficult engineering challenges for you. Complexities like creating a rich user interface, configuring SSO, managing user sessions, and implementing authorization are all handled **out-of-the-box**.

This allows your developers to bypass these hurdles and focus exclusively on what they do best: **building amazing and impactful agents using the ADK.**

### Features at a Glance

* **Enterprise-Ready Authentication 🔐:** Material AI comes with a built-in, configurable authentication module that seamlessly integrates with customer infrastructure and simplifies the process of setting up SSO.
* **A Rich, Gemini-like User Interface ✨:** Material AI delivers a modern, intuitive, and production-ready UI inspired by the Google Gemini app, providing a professional and engaging front-end for your agents.
* **User Interface Customization🎨:** Customize User Interface seamlessly as per customer's requirement.
* **Extensible Custom Functionality 🛠️:** Our framework introduces an extensible backend layer, allowing you to easily add custom business logic and integrate with other internal or third-party APIs.
* **Robust Session Management & Authorization 👤:** Material AI includes a sophisticated system for managing user sessions and a granular authorization layer to define roles and permissions, ensuring only authorized users can interact with the application.

-----

## 🚀 Setting Up Locally

Follow these steps to get your local development environment running.

### Prerequisites

Make sure you have the following installed on your system:

  * **Python** (version 3.9 or higher)
  * **uv** (a fast Python package installer)
  * **make** (a fast command line interface)
  * **nodejs** (https://nodejs.org/en)

If you don't have `uv`, you can install it quickly. On macOS and Linux, run `curl -LsSf https://astral.sh/uv/install.sh | sh`. For Windows, use `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`.

If you don't have `make`, you can install it quickly. On macOS and Linux, run `apt-get update && apt-get install -y make`.

-----

### Installation Steps

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/muralimanoharv/material-ai.git
    cd material-ai
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    # Create the virtual environment
    uv venv

    # Activate it (the command differs by shell)
    source .venv/bin/activate
    ```

3.  **Install the dependencies:**

    ```bash
    uv sync
    ```

4.  **Set up environment variables:**
    By default, the application is configured to use **Google OAuth** for SSO. Before running the app, you will need to set up an **OAuth 2.0 Client ID** in the [Google Cloud Console](https://console.cloud.google.com/apis/credentials) to get your credentials.

    You will also need GEMINI API KEY Go to https://aistudio.google.com/apikey to generate API KEY

    Create a file named `.env` in the root of the project by copying the example file:

    ```bash
    cp .env.example .env
    ```

    Open the newly created `.env` file and fill in the required values. It will look like this:

    ```ini
    # Single Sign-On (SSO) Configuration
    SSO_CLIENT_ID="YOUR_SSO_CLIENT_ID"
    SSO_CLIENT_SECRET="YOUR_SSO_CLIENT_SECRET"

    # WARNING: This configuration is for local development ONLY.
    # For production, this MUST be updated to a public, HTTPS-enabled URL.
    # SSO redirects over non-secure (http) connections are a security risk.
    SSO_REDIRECT_URI="http://localhost:8080/auth"

    # Session Management
    SSO_SESSION_SECRET_KEY="GENERATE_A_STRONG_RANDOM_SECRET_KEY"

    # Application Configuration
    CONFIG_PATH="config.ini"

    # Google Configuration
    GOOGLE_GENAI_USE_VERTEXAI=FALSE
    GOOGLE_API_KEY="YOUR_GEMINI_API_KEY"

    # WARNING: This configuration uses a local file-based database suitable only for development.
    # DO NOT use this in a production environment. Use a managed database instead.
    ADK_SESSION_DB_URL="sqlite:///./my_agent_data.db"

    ```

5.  **Run the application:**

    ```bash
    make run
    ```

    The application should now be running on `http://127.0.0.1:8080`.
    Access swagger API docs on `http://127.0.0.1:8080/docs`.

5.  **Debug the application:**

    In order to debug you need to first create vscode debug config under `.vscode/launch.json`
    ```json
    {
        "version": "0.2.0",
        "configurations": [
        
            {
                "name": "Python Debugger: Remote Attach",
                "type": "debugpy",
                "request": "attach",
                "connect": {
                    "host": "localhost",
                    "port": 5678
                },
                "pathMappings": [
                    {
                        "localRoot": "${workspaceFolder}",
                        "remoteRoot": "."
                    }
                ]
            }
        ]
    }
    ```

    ```bash
    make debug
    ```

    The application should now be running on `http://127.0.0.1:8080` and debug port running on `http://127.0.0.1:5678`.

    Attach python remote debugger using vscode debug tools

---
## Docker for Development 🐳

If you are like me lazy to install all dependencies, don't worry we got you covered

### Prerequisites

* You must have **Docker** and **Docker Compose** installed on your system.
* You have cloned this repository.

### Setup Instructions

**1. Configure Environment Variables**

The application requires environment variables to run. We've included an example file to get you started.

First, copy the example `.env` file:
```bash
cp .env.example .env
````

Next, open the newly created `.env` file and fill in the required values.

**2. Build and Run the Application**

Once your `.env` file is configured, you can start the application with a single command:

```bash
docker compose up
```

This command will build the necessary Docker images and start all the services. You can add the `-d` flag to run the containers in the background (detached mode).

### Useful Docker Commands

  * **Run in the background:**
    ```bash
    docker compose up -d
    ```
  * **Force a rebuild of the images:**
    ```bash
    docker compose up --build
    ```
  * **Stop and remove the containers:**
    ```bash
    docker compose down
    ```
-----

## 🤖 Creating Your First Agent

Adding new agents to Material AI is designed to be simple and intuitive, following a "convention over configuration" approach.

### The `agents` Directory

To create a new agent, all you need to do is **add a new Python file inside the `src/material_ai/agents/<agent_name>/agent.py` directory**.

Material AI automatically scans this directory on startup. Any valid agent definition it finds will be dynamically loaded and displayed in the UI, with no manual registration or configuration files needed. This allows you to focus purely on building your agent's logic.

### Example Agent

Here is a simple example of what an agent file might look like. You could save this as `src/material_ai/agents/greeting_agent/agent.py`:

Make sure to provide necessary environment variables for ADK

```ini
GOOGLE_GENAI_USE_VERTEXAI=FALSE/TRUE
GOOGLE_API_KEY="YOUR_GEMINI_API_KEY"
```
Go to https://aistudio.google.com/apikey to generate API KEY

```python
# src/material_ai/agents/greeting_agent/agent.py

from google.adk.agents import Agent
from material_ai.oauth import oauth_user_details_context

def say_hello():
    return {
        "description": "Hi, what can I do for you today?"
    }

def who_am_i():
    user_details = oauth_user_details_context.get() # Get user details like uid, email, full name etc...
    return user_details


# Define the agent itself, giving it a name and description.
# The agent will automatically use the tools you provide in the list.
root_agent = Agent(
    name="greeting_agent",
    model="gemini-2.0-flash",
    description="An agent that can greet users.",
    instruction="""
    Use say_hello tool to greet user, If user asks about himself use who_am_i tool
    """,
    tools=[say_hello, who_am_i],
)
```

Since Material AI takes care of authentication & authorization you can easily retrieve user information. 

We can use this information to do validations, authorizations and also maybe send email or push notifications.

Make sure to expose agent under `__init__.py` under `src/material_ai/agents/greeting_agent/__init__.py`

```python
from . import agent
```

Once you save this file, the next time you run the application, a new "Greeting Agent" will automatically appear in the UI, ready to be used.

---

Excellent. This is a critical section for developers looking to adapt your project. Here is the "Configuring SSO" section for your README, written based on the details you provided.

-----

## 🔐 Configuring Single Sign-On (SSO)

Material AI is built to be flexible, allowing you to use the default Google SSO for quick setups or integrate a custom SSO provider for specific customer needs.

### Default Configuration (Google OAuth)

By default, Material AI uses **Google OAuth 2.0** for authentication. For most use cases, especially local development, you simply need to update your `.env` file with the correct Google OAuth credentials.

The source code for this default implementation is available for reference in `src/material_ai/oauth/google_oauth.py`.

### Adding a Custom SSO Provider

For customer deployments that require integration with a different identity provider (e.g., Azure AD, Okta), Material AI provides a streamlined, one-time setup process. This is designed to be easy for developers.

Follow these two steps to add a new SSO provider:

#### 1\. Implement the `IOAuthService` Interface

First, create a new class for your SSO provider (e.g., `AzureOAuthService`). This class **must** implement the `IOAuthService` interface to ensure it's compatible with the application's authentication flow.

You can find the interface definition, which outlines all the required methods you need to implement, in the following file:
`src/material_ai/oauth/interface.py`

Here is a basic skeleton for what your custom service class would look like:

```python
# src/material_ai/oauth/azure_oauth.py

from .interface import IOAuthService

class AzureOAuthService(IOAuthService):
    """
    Custom SSO implementation for Azure Active Directory.
    """
    # You must implement all methods defined in the IOAuthService interface,
    # such as sso_get_redirection_url(), sso_get_access_token(), sso_get_new_access_token(), etc.
    ...

```

#### 2\. Register Your New Service

Next, you need to tell Material AI to use your new service. Open the file `src/material_ai/oauth/oauth.py` and modify the `get_oauth()` function to instantiate your custom class instead of the default `GoogleOAuthService`.

```python
# src/material_ai/oauth/oauth.py
from .google_oauth import GoogleOAuthService
# Import your new custom service here
from .azure_oauth import AzureOAuthService 

def get_oauth() -> IOAuthService:
    global _oauth_instance
    with _lock:
        if _oauth_instance is None:
            # Replace the default service with your new implementation
            
            # --- BEFORE ---
            # _oauth_instance = GoogleOAuthService()
            
            # --- AFTER ---
            _oauth_instance = AzureOAuthService()
            
        return _oauth_instance
```

Once this change is made, the entire application will use your custom SSO provider for all authentication workflows.

---

## 🎨 Customizing the User Interface

Material AI's front end is designed to be easily customized and white-labeled to meet specific customer requirements. You can adjust core application settings and visual themes by modifying two key files.

### 1. General Application Configuration

For high-level UI customizations, you can modify the configuration object in the following file:
`src/material_ai/ui/ui_config.yaml`

This file allows you to easily change key aspects of the user experience. A high-level overview of what you can customize includes:

* **Application Title & Text:** Update the main `title` of the application, the initial `greeting` message on the chat screen, and other default text strings.
* **AI Model Selection:** Define the list of available AI `models` that users can choose from, including their display names and descriptive taglines.
* **User Feedback System:** Configure the `feedback` options, such as the categories presented to users when they provide a negative rating.

### 2. Customizing Themes (Light & Dark Mode)

To align the application's look and feel with customer branding, you can customize the color palettes in this file:
`src/material_ai/ui/ui_config.yaml`

This file defines the `lightPalette` and `darkPalette` under theme property used for the application's light and dark modes. You can easily change the color values for various UI elements, including:

* Primary colors (for buttons and accents)
* Background and paper colors
* Text colors for different headings and paragraphs

This allows you to create a completely bespoke visual experience based on customer UX preferences.

### ✨ Pro Tip: Generating Themes with AI
Struggling to come up with the perfect color scheme? You can **use Gemini to create beautiful color palettes** for the application.

For example, try a prompt like: *"Create a professional color palette for a web application's light and dark theme. The primary color should be a shade of teal."* You can then use the suggested hex codes in your `themes.js` file.

---

## Deployment 🚀

This project is deployed using a `Makefile` command that automates the build and deployment process.

### 1\. Provide Appropriate Permissions
Make sure to run `chmod +x ./scripts` and provide permissions to execute shell scripts


### 2\. Deploy the Application

Once your `.env` file is configured, run the following command to build and deploy the application:

```bash
make deploy
```

### 3\. Teardown the Application

Once your `.env` file is configured, run the following command to teardown the application:

```bash
make teardown
```

### 4\. Steps to add additional roles to cloud run service account
In order to add additional permissions to cloud run service account you
can modify the crun roles under `scripts/main.tf -> sa_permissions`

---
## 🐞 Reporting Issues and Feature Requests

We welcome your contributions! If you encounter a bug or have an idea for a new feature, the best way to let us know is by opening an issue on our GitHub repository.

All bug reports and enhancement requests can be raised directly on the **[GitHub Issues page](https://github.com/muralimanoharv/material-ai/issues)**.

* **For Bug Reports:** When reporting a bug, please include a clear title, a detailed description of the problem, steps to reproduce it, and what you expected to happen.
* **For Feature Requests:** If you're proposing an enhancement, please describe the problem you're trying to solve and provide a clear explanation of the desired functionality.

We appreciate you taking the time to help improve Material AI!
