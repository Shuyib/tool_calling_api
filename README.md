[![Agent Continuous Integration/Continuos Delivery](https://github.com/Shuyib/tool_calling_api/actions/workflows/python-app.yml/badge.svg)](https://github.com/Shuyib/tool_calling_api/blob/main/.github/workflows/python-app.yml)
# Exploring function calling 🗣️ 🤖 🔉 with Python and ollama 🦙
Function-calling with Python and ollama. We are going to use the Africa's Talking API to send airtime and messages to a phone number using Natural language. Thus, creating an generative ai agent. Here are examples of prompts you can use to send airtime to a phone number:
- Send airtime to xxxxxxxxx2046 and xxxxxxxxx3524 with an amount of 10 in currency KES
- Send a message to xxxxxxxxx2046 and xxxxxxxxx3524 with a message "Hello, how are you?", using the username "username".
- Dial a USSD code like *123# on xxxxxxxxx2046
- Send 500MB of data to xxxxxxxxx2046 on provider safaricom
- Call xxxxxxxxx2046 from +254700000001

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
├── docker-compose.yml - use the ollama project and gradio dashboard.   
├── docker-compose-codecarbon.yml - use the codecarbon project, ollama and gradio dashboard.   
├── .env - This file contains the environment variables for the project. (Not included in the repository)   
├── app.py - the function_call.py using gradio as the User Interface.   
├── Makefile - This file contains the commands to run the project.   
├── README.md - This file contains the project documentation. This is the file you are currently reading.   
├── requirements.txt - This file contains the dependencies for the project.   
├── requirements-dev.txt - This filee contains the dependecies for the devcontainer referencing `requirements.txt`    
├── summary.png - How function calling works with a diagram.   
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

NB: You'll need to have deployed ollama elsewhere as an example [here](https://vast.ai/) or [here](https://runpod.io/). Make edits to the app.py file to point to the ollama server. You can use the OpenAI SDK to interact with the ollama server. An example can be found [here](https://github.com/pooyahrtn/RunpodOllama).

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

### Responsible AI Practices
This project implements several responsible AI practices:
- All test data is anonymized to protect privacy.
- Input validation to prevent misuse (negative amounts, spam detection).
- Handling of sensitive content and edge cases.
- Comprehensive test coverage for various scenarios.
- Secure handling of credentials and personal information.

![Process Summary](summary.png)

## Use cases
    * Non-Technical User Interfaces: Simplifies the process for non-coders to interact with APIs, making it easier for them to send airtime and messages without needing to understand the underlying code.
    * Customer Support Automation: Enables customer support teams to quickly send airtime or messages to clients using natural language commands, improving efficiency and response times.
    * Marketing Campaigns: Facilitates the automation of promotional messages and airtime rewards to customers, enhancing engagement and retention.
    * Emergency Notifications: Allows rapid dissemination of urgent alerts and notifications to a large number of recipients using simple prompts.
    * Educational Tools: Provides a practical example for teaching how to integrate APIs with natural language processing, which can be beneficial for coding bootcamps and workshops.
    * Multilingual Support: Supports multiple languages when sending messages and airtime, making it accessible to a diverse range of users. Testing for Arabic, French, English and Portuguese.

## Limitations
- The project is limited to sending airtime, searching for news, and messages using the Africa's Talking API. The functionality can be expanded to include other APIs and services.

- The jailbreaking of the LLMS is a limitation. The LLMS are not perfect and can be manipulated to produce harmful outputs. This can be mitigated by using a secure environment and monitoring the outputs for any malicious content. However, the Best of N technique and prefix injection were effective in changing model behavior.

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
