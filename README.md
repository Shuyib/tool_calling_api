# Exploring function calling 🗣️ 🤖 with Python and ollama 🦙
Function-calling with Python and ollama. We are going to use the Africa's Talking API to send airtime and messages to a phone number using Natural language. Here are examples of prompts you can use to send airtime to a phone number:
- Send airtime to xxxxxxxxx2046 and xxxxxxxxx3524 with an amount of 10 in currency KES
- Send a message to xxxxxxxxx2046 and xxxxxxxxx3524 with a message "Hello, how are you?", using the username "username".

NB: The phone numbers are placeholders for the actual phone numbers.
You need some VRAM to run this project. You can get VRAM from [here](https://vast.ai/)
We recommend 2-8GB of VRAM for this project. It can run on CPU however, I recommend smaller models for this.   
Mistral 7B, **llama 3.2 3B** and llama3.1 8B are the recommended models for this project.   
Ensure ollama is installed on your laptop/server and running before running this project. You can install ollama from [here](ollama.com)   
Learn more about tool calling <https://gorilla.cs.berkeley.edu/leaderboard.html>


## Table of contents
- [File structure](#file-structure)
- [Installation](#installation)
- [Run in Docker](#run-in-docker)
- [Usage](#usage)
- [Use cases](#use-cases)
- [Contributing](#contributing)
- [License](#license)    


## File structure
.   
├── Dockerfile - template to run the project in one shot.    
├── docker-compose.yml - use the codecarbon project and gradio dashboard.   
├── app.py - the function_call.py using gradio as the User Interface.  
├── Makefile - This file contains the commands to run the project.   
├── README.md - This file contains the project documentation. This is the file you are currently reading.       
├── requirements.txt - This file contains the dependencies for the project.  
├── summary.png - How function calling works with a diagram.   
└── utils - This directory contains the utility files for the project.      
    ├── __init__.py - This file initializes the utils directory as a package.    
    ├── function_call.py - This file contains the code to call a function using LLMs.       
    └── send_airtime.py - This file contains the code to send airtime to a phone number.       
    
## Installation
The project uses python 3.12. To install the project, follow the steps below:    

- Clone the repository
```bash
git clone
```
- Change directory to the project directory
```bash
cd Function-calling
```   
Create a virtual environment
```bash
python3 -m venv venv
```
Activate the virtual environment
```bash
source venv/bin/activate
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

-linting dockerfile

```bash
make docker_run_test
```

- Build the Docker image
```bash
make docker_build
```

- Run the Docker image
```bash
make docker_run
```


## Usage
This project uses LLMs to send airtime to a phone number. The difference is that we are going to use the Africa's Talking API to send airtime to a phone number using Natural language. Here are examples of prompts you can use to send airtime to a phone number:    
- Send airtime to xxxxxxxxxx046 and xxxxxxxxxx524 with an amount of 10 in currency KES.   
- Send a message to xxxxxxxxxx046 and xxxxxxxxxx524 with a message "Hello, how are you?", using the username "username".

![Process Summary](summary.png)

## Use cases
    * Non-Technical User Interfaces: Simplifies the process for non-coders to interact with APIs, making it easier for them to send airtime and messages without needing to understand the underlying code.    
    * Customer Support Automation: Enables customer support teams to quickly send airtime or messages to clients using natural language commands, improving efficiency and response times.    
    * Marketing Campaigns: Facilitates the automation of promotional messages and airtime rewards to customers, enhancing engagement and retention.    
    * Emergency Notifications: Allows rapid dissemination of urgent alerts and notifications to a large number of recipients using simple prompts.    
    * Educational Tools: Provides a practical example for teaching how to integrate APIs with natural language processing, which can be beneficial for coding bootcamps and workshops.    

## Contributing
Contributions are welcome. If you would like to contribute to the project, you can fork the repository, create a new branch, make your changes and then create a pull request.

## License
[License information](https://github.com/Shuyib/tool_calling_api/blob/main/LICENSE).
