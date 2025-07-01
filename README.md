[![Agent Continuous Integration/Continuos Delivery](https://github.com/Shuyib/tool_calling_api/actions/workflows/python-app.yml/badge.svg)](https://github.com/Shuyib/tool_calling_api/blob/main/.github/workflows/python-app.yml)
# Exploring function calling 🗣️ 🤖 🔉 with Python and ollama 🦙
Function-calling with Python and ollama. We are going to use the Africa's Talking API to send airtime and messages to a phone number using Natural language. Thus, creating an generative ai agent. 

## Available Services
✅ **Currently Working**: SMS/Messages, Airtime, Voice Calls with Text-to-Speech**  
⚠️ **Requires Approval**: Voice Calls (production account), Mobile Data (business approval)

Here are examples of prompts you can use:
- Send airtime to xxxxxxxxx2046 and xxxxxxxxx3524 with an amount of 10 in currency KES
- Send a message to xxxxxxxxx2046 and xxxxxxxxx3524 with a message "Hello, how are you?", using the username "username".
- Dial a USSD code like *123# on xxxxxxxxx2046 *(requires approval)*
- Send 500MB of data to xxxxxxxxx2046 on provider safaricom *(requires business approval)*
- Call xxxxxxxxx2046 from +254700000001 *(requires production account with registered caller ID)*
- **NEW**: Make a voice call from +254700000001 to +254712345678 and say "Hello, this is a test message" *(with callback server setup)*

NB: The phone numbers are placeholders for the actual phone numbers.
You need some VRAM to run this project. You can get VRAM from [here](https://vast.ai/) or [here](https://runpod.io?ref=46wgtjpg)
We recommend 400MB-8GB of VRAM for this project. It can run on CPU however, I recommend smaller models for this.

[Mistral 7B](https://ollama.com/library/mistral), **llama 3.2 3B/1B**, [**Qwen 2.5: 0.5/1.5B**](https://ollama.com/library/qwen2.5:1.5b), [nemotron-mini 4b](https://ollama.com/library/nemotron-mini) and [llama3.1 8B](https://ollama.com/library/llama3.1) are the recommended models for this project. As for the VLM's (Vision Language Models), in the workflow consider using [llama3.2-vision](https://ollama.com/library/llama3.2-vision) or [Moondream2](https://ollama.com/library/moondream) or [olm OCR](https://huggingface.co/bartowski/allenai_olmOCR-7B-0225-preview-GGUF).        

Ensure ollama is installed on your laptop/server and running before running this project. You can install ollama from [here](ollama.com)
Learn more about tool calling <https://gorilla.cs.berkeley.edu/leaderboard.html>


## Table of contents
- [File structure](#file-structure)
- [Attribution](#atrribution)
- [Installation](#installation)
- [Run in Docker](#run-in-docker)
- [Voice Functionality Setup](#voice-functionality-setup)
- [Usage](#usage)
- [Use cases](#use-cases)
- [Responsible AI Practices](#responsible-ai-practices)
- [Limitations](#limitations)
- [Contributing](#contributing)
- [License](#license)


## File structure   
.   
├── Dockerfile.app - template to run the gradio dashboard.      
├── Dockerfile.ollama - template to run the ollama server.   
├── Dockerfile.voice - template to run the voice callback server.   
├── docker-compose.yml - use the ollama project, gradio dashboard, and voice server.   
├── docker-compose-codecarbon.yml - use the codecarbon project, ollama and gradio dashboard.   
├── DOCKER_VOICE_SETUP.md - Comprehensive guide for Docker voice functionality setup.   
├── .env - This file contains the environment variables for the project. (Not included in the repository)   
├── app.py - the function_call.py using gradio as the User Interface.   
├── Makefile - This file contains the commands to run the project.   
├── README.md - This file contains the project documentation. This is the file you are currently reading.   
├── requirements.txt - This file contains the dependencies for the project.   
├── requirements-dev.txt - This filee contains the dependecies for the devcontainer referencing `requirements.txt`    
├── summary.png - How function calling works with a diagram.   
├── setup_voice_server.md - Step-by-step guide for setting up voice callbacks with text-to-speech.   
├── voice_callback_server.py - Flask server that handles voice callbacks for custom text-to-speech messages.   
├── tests - This directory contains the test files for the project.   
│   ├── __init__.py - This file initializes the tests directory as a package.      
│   ├── test_cases.py - This file contains the test cases for the project.   
│   └── test_run.py - This file contains the code to run the test cases for the function calling LLM.   
└── utils - This directory contains the utility files for the project.   
│    ├── __init__.py - This file initializes the utils directory as a package.   
│    ├── function_call.py - This file contains the code to call a function using LLMs.   
│    └── communication_apis.py - This file contains the code to do with communication apis & experiments.   
|    └── models.py - This file contains pydantic schemas for vision models.   
|    └── constants.py - This file contains system prompts to adjust the model's behavior.   
└── voice_stt_mode.py - Gradio tabbed interface with Speech-to-text interface that allows edits and a text interface.   

## Attribution
* This project uses the Qwen2.5-0.5B model developed by Alibaba Cloud under the Apache License 2.0. The original project can be found at [Qwen technical report](https://arxiv.org/abs/2412.15115)
* Inspired by this example for the [Groq interface STT](https://github.com/bklieger-groq/gradio-groq-basics)
* Microsoft Autogen was used to simulate multistep interactions. The original project can be found at [Microsoft Autogen](https://github.com/microsoft/autogen)
* The project uses the Africa's Talking API to send airtime and messages to phone numbers. Check them out on this website [Africa's Talking API](https://africastalking.com/)
* Ollama for model serving and deployment. The original project can be found at [Ollama](https://ollama.com/)
* The project uses the Gradio library to create a user interface for the function calling LLM. The original project can be found at [Gradio](https://gradio.app/)
* The Text-to-Speech interface uses Edge TTS by Microsoft. The original project can be found at [Edge TTS](https://github.com/rany2/edge-tts). The voice chosen is Rehema which is a voice from Tanzania.


### License

This project is licensed under the Apache License 2.0. See the [LICENSE](./LICENSE) file for more details.

## Installation
The project uses python 3.12. To install the project, follow the steps below:

- Clone the repository
```bash
git clone https://github.com/Shuyib/tool_calling_api.git
```
- Change directory to the project directory
```bash
cd tool_calling_api
```
Create a virtual environment
```bash
python3 -m venv .venv
```
Activate the virtual environment
```bash
source .venv/bin/activate
```
Confirm if steps of Makefile are working
```bash
make -n
```

- Install the dependencies
```bash
make install
```
- Run the project

```bash
make run
```
Long way to run the project

- Change directory to the utils directory
```bash
cd utils
```
- Run the function_call.py file
```bash
python function_call.py
```
- Run the Gradion UI instead
```bash
python ../app.py
```

## Run in Docker
To run the project in Docker, follow the steps below:

### Standard Setup
NB: You'll need to have deployed ollama elsewhere as an example [here](https://vast.ai/) or [here](https://runpod.io/). Make edits to the app.py file to point to the ollama server. You can use the OpenAI SDK to interact with the ollama server. An example can be found [here](https://github.com/pooyahrtn/RunpodOllama).

- Linting dockerfile

```bash
make docker_run_test
```

- Build and run the Docker image

```bash
make docker_run
```

### Voice Functionality Setup
For the new voice features (text-to-speech and audio playback), additional setup is required:

1. **Basic Docker Setup**: Follow the standard setup above
2. **Voice Server Configuration**: The updated Docker setup includes a dedicated voice callback server
3. **External Access**: For production use, set up ngrok or deploy with proper domain

See [DOCKER_VOICE_SETUP.md](DOCKER_VOICE_SETUP.md) for detailed voice functionality setup instructions.

**Quick Voice Setup for Development:**
```bash
# Start all services including voice server
docker-compose up --build

# In a separate terminal, expose voice server with ngrok
ngrok http 5001

# Update environment variable with ngrok URL
export VOICE_CALLBACK_URL="https://your-ngrok-url.ngrok.io"

# Restart the app to use new callback URL
docker-compose restart app
```

- Linting dockerfile

```bash
make docker_run_test
```

- Build and run the Docker image

```bash
make docker_run
```

Notes:
-  The .env file contains the environment variables for the project. You can create a .env file and add the following environment variables:

```bash
echo "AT_API_KEY = yourapikey" >> .env
echo "AT_USERNAME = yourusername" >> .env
echo "GROQ_API_KEY = yourgroqapikey" >> .env
echo "LANGTRACE_API_KEY= yourlangtraceapikey" >> .env
echo "VOICE_CALLBACK_URL = https://your-ngrok-url.ngrok.io" >> .env
echo "TEST_PHONE_NUMBER = yourphonenumber" >> .env
echo "TEST_PHONE_NUMBER_2 = yourphonenumber" >> .env
echo "TEST_PHONE_NUMBER_3 = yourphonenumber" >> .env
```
- The Dockerfile creates 2 images for the ollama server and the gradio dashboard. The ollama server is running on port 11434 and the gradio dashboard is running on port 7860 . You can access the gradio dashboard by visiting <http://localhost:7860> in your browser & the ollama server by visiting <http://localhost:11434> in your browser. They consume about 2.72GB of storage in the container.
- The docker-compose.yml file is used to run the ollama server and the gradio dashboard. The docker-compose-codecarbon.yml file is used to run the ollama server, the gradio dashboard and the codecarbon project.
- You can learn more about how to make this system even more secure. Do this [course](https://www.kaggle.com/learn-guide/5-day-genai#GenAI).


## Run in runpod.io
Make an account if you haven't already. Once that's settled.

- Click on Deploy under Pods.
- Select the cheapest option pod to deploy for example RTX 2000 Ada.
- This will create a jupyter lab instance.
- Follow the Installation steps in the terminal available. Until the make install.
- Run this command. Install ollama and serve it then redirect output to a log file.

```bash
curl -fsSL https://ollama.com/install.sh | sh && ollama serve > ollama.log 2>&1 &
```
- Install your preferred model in the same terminal.

```bash
ollama run qwen2.5:0.5b
```
- Export your credentials but, if you are using a .env file, you can skip this step. It will be useful for Docker.

```bash
export AT_API_KEY=yourapikey
export AT_USERNAME=yourusername
export GROQ_API_KEY=yourgroqapikey
export LANGTRACE_API_KEY=yourlangtraceapikey
export VOICE_CALLBACK_URL=https://your-ngrok-url.ngrok.io
export TEST_PHONE_NUMBER=yourphonenumber
export TEST_PHONE_NUMBER_2=yourphonenumber
export TEST_PHONE_NUMBER_3=yourphonenumber
```
- Continue running the installation steps in the terminal.
- Send your first message and airtime with an LLM. 🌠

Read more about setting up ollama and serveless options <https://blog.runpod.io/run-llama-3-1-405b-with-ollama-a-step-by-step-guide/> & <https://blog.runpod.io/run-llama-3-1-with-vllm-on-runpod-serverless/>

## Usage
This project uses LLMs to send airtime to a phone number. The difference is that we are going to use the Africa's Talking API to send airtime to a phone number using Natural language. Here are examples of prompts you can use to send airtime to a phone number:
- Send airtime to xxxxxxxxxx046 and xxxxxxxxxx524 with an amount of 10 in currency KES.
- Send a message to xxxxxxxxxx046 and xxxxxxxxxx524 with a message "Hello, how are you?", using the username "username".

## Updated Usage Instructions
- The app now supports both Text and Voice input tabs.
- In the Voice Input tab, record audio and click "Transcribe" to preview the transcription. Then click "Process Edited Text" to execute voice commands.
- In the Text Input tab, directly type commands to send airtime or messages or to search news.
- An autogen agent has been added to assist with generating translations to other languages. Note that this uses an evaluator-optimizer model and may not always provide accurate translations. However, this paradigm can be used for code generation, summarization, and other tasks.
- Text-to-Speech (TTS) has been added to the app. You can listen to the output of the commands.

### NEW: Voice Calls with Custom Text-to-Speech 🔊
The app now supports making voice calls that speak custom messages instead of the default Africa's Talking greeting. This provides a more personalized experience for the call recipient.

**How it Works:**

1.  **Initiate the Call**: When you use a command like:
    `"Make a voice call from +254700000001 to +254712345678 and say 'Hello, this is a test message from our new system!'"`,
    the `make_voice_call_with_text` function in `utils/communication_apis.py` is triggered.

2.  **Message Storage**:
    *   This function first generates a unique session ID for the call.
    *   It then makes an HTTP POST request to a local Flask server (`voice_callback_server.py`) to store the message ("Hello, this is a test message...") and the chosen voice type (e.g., "woman") associated with this session ID.
    *   The `VOICE_CALLBACK_URL` environment variable (defaulting to `http://localhost:5001` if not set) tells `make_voice_call_with_text` where to send this information (e.g., `http://localhost:5001/voice/store`).

3.  **Africa's Talking Call Placement**:
    *   `make_voice_call_with_text` then instructs the Africa's Talking API to place the call.
    *   Crucially, your Africa's Talking account **must be configured with a public callback URL** for voice services. This is where the Africa's Talking platform will send a request when the call is answered.

4.  **Fetching the Custom Message (Callback)**:
    *   When the recipient answers, the Africa's Talking platform makes an HTTP GET request to your configured public callback URL (e.g., `https://your-unique-ngrok-id.ngrok.io/voice/callback?sessionId=xxx...`).
    *   This public URL should be an ngrok (or similar tunneling service) endpoint that forwards the request to your local `voice_callback_server.py` running on port 5001 (or the port you've configured).
    *   The `voice_callback_server.py` (specifically its `/voice/callback` endpoint) receives this request, extracts the `sessionId`, retrieves the stored message and voice type for that session, and dynamically generates an XML response.

5.  **Text-to-Speech**:
    *   The XML response tells Africa's Talking to use its Text-to-Speech engine to say your custom message to the recipient in the specified voice.
    ```xml
    <Response>
        <Say voice="woman">Hello, this is a test message from our new system!</Say>
    </Response>
    ```

**Setup Requirements**:

1.  **Run the Local Callback Server**:
    Start the Flask server:
    ```bash
    python voice_callback_server.py
    ```
    This server typically runs on `http://localhost:5001`.

2.  **Expose the Local Server Publicly**:
    Use ngrok (or a similar service) to create a public URL that tunnels to your local server:
    ```bash
    ngrok http 5001
    ```
    Ngrok will provide you with a public HTTPS URL (e.g., `https://<unique-id>.ngrok.io`).

3.  **Configure Africa's Talking Dashboard**:
    *   Log in to your Africa's Talking account.
    *   Go to Voice > Settings (or similar section for callback URLs).
    *   Set your **Voice Callback URL** to the public ngrok URL, ensuring it points to the correct endpoint, typically `/voice/callback`. For example: `https://<unique-id>.ngrok.io/voice/callback`.
    *   **Important**: The `make_voice_call_with_text` function itself *does not* send this public callback URL to Africa's Talking when placing the call; it relies on your dashboard configuration.

4.  **Environment Variable (Optional but Recommended)**:
    While `make_voice_call_with_text` defaults to `http://localhost:5001` for *storing* the message locally, you can set the `VOICE_CALLBACK_URL` environment variable if your `voice_callback_server.py` runs on a different local address or port. This variable is for the *internal* communication between `communication_apis.py` and `voice_callback_server.py`, not for the Africa's Talking platform callback.
    Example for `.env` file:
    ```
    VOICE_CALLBACK_URL=http://localhost:5001
    ```

**Using the Feature**:
Once set up, you can use natural language commands like:
`"Call +254712345678 from my Africa's Talking number +254700000000 and tell them 'Your package has arrived.' using a male voice."`

The system will handle the rest, ensuring your custom message is played.

##### NEW: Voice Calls with Custom Text-to-Speech ✨
- **Status**: Fully functional with callback server setup
- **Features**: 
  - Speak custom messages instead of default Africa's Talking greeting
  - Support for both "man" and "woman" voice types
  - Real-time message storage and retrieval via callback system
- **Setup**: Requires `voice_callback_server.py` to be running, ngrok (or similar) for a public callback URL, and correct configuration in the Africa's Talking dashboard. See detailed instructions above and in [setup_voice_server.md](setup_voice_server.md).
- **Note**: This works even with test credentials for the voice call initiation part, as long as the callback mechanism is correctly configured.

#### Airtime Distribution 💰
- **Status**: Limited sandbox functionality - requires production credentials for full operation
- **Issue**: Airtime connector only works with production applications, not sandbox API keys
- **Requirements**:
  1. Production application with valid API credentials
  2. Manual activation by emailing airtime@africastalking.com
  3. Testing limited to Africa's Talking simulator (not real devices)
- **Note**: While airtime functions exist in sandbox, actual distribution requires production setup

#### Mobile Data Bundles 📱
- **Status**: Requires formal business approval
- **Issue**: Service disabled for all accounts for security reasons
- **Approval Process**: 
  1. Write formal letter on company letterhead (stamped & signed by management)
  2. Fill out Africa's Talking contact form
  3. Sign service agreement
  4. Submit documentation to airtime@africastalking.com
- **Reference**: [Mobile Data Activation Guide](https://help.africastalking.com/en/articles/8287530-how-do-i-activate-mobile-data-on-my-account)

### Technical Implementation Status 🔧
All API integrations are **technically correct** and ready for production use once account approvals are obtained. The code implements proper parameter handling and error management for all services.

## Use cases
    * Non-Technical User Interfaces: Simplifies the process for non-coders to interact with APIs, making it easier for them to send airtime and messages without needing to understand the underlying code.
    * Customer Support Automation: Enables customer support teams to quickly send airtime or messages to clients using natural language commands, improving efficiency and response times.
    * Marketing Campaigns: Facilitates the automation of promotional messages and airtime rewards to customers, enhancing engagement and retention.
    * Emergency Notifications: Allows rapid dissemination of urgent alerts and notifications to a large number of recipients using simple prompts.
    * Educational Tools: Provides a practical example for teaching how to integrate APIs with natural language processing, which can be beneficial for coding bootcamps and workshops.
    * Multilingual Support: Supports multiple languages when sending messages and airtime, making it accessible to a diverse range of users. Testing for Arabic, French, English and Portuguese.

## Limitations

### Africa's Talking API Limitations
- **Voice Calls**: Requires production account with registered caller ID numbers. Test credentials will return "Invalid callerId" errors.
- **Airtime Distribution**: While sandbox testing is possible, actual airtime distribution requires production credentials and manual activation. Test accounts have limited functionality.
- **Mobile Data**: Requires formal business approval process including company documentation and service agreements. Currently disabled for all accounts for security reasons.
- **SMS**: Fully functional with both test and production credentials.

### Technical Limitations
- The project is primarily designed for Africa's Talking API services. While the functionality can be expanded to include other APIs and services, current implementation focuses on communication services.

### LLM Security Considerations
- The jailbreaking of the LLMs is a limitation. The LLMs are not perfect and can be manipulated to produce harmful outputs. This can be mitigated by using a secure environment and monitoring the outputs for any malicious content. However, the Best of N technique and prefix injection were effective in changing model behavior.

### Testing Coverage
- A small number of test cases were used to test the project. More test cases can be added to cover a wider range of scenarios and edge cases.

## Contributing
Contributions are welcome. If you would like to contribute to the project, you can fork the repository, create a new branch, make your changes and then create a pull request.

### Testing Guidelines
When contributing, please ensure:
- All test data uses anonymized placeholders
- Edge cases and invalid inputs are properly tested
- Sensitive content handling is verified
- No real personal information is included in tests

## License
[License information](https://github.com/Shuyib/tool_calling_api/blob/main/LICENSE).
