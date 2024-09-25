# Exploring function calling 🗣️ 🤖 with Python and ollama 🦙
Function-calling with Python and ollama. We are going to use the Africa's Talking API to send airtime and messages to a phone number using Natural language. Here are examples of prompts you can use to send airtime to a phone number:
- Send airtime to xxxxxxxxx2046 and xxxxxxxxx3524 with an amount of 10 in currency KES
- Send a message to xxxxxxxxx2046 and xxxxxxxxx3524 with a message "Hello, how are you?", using the username "username".

NB: The phone numbers are placeholders for the actual phone numbers.
You need some VRAM to run this project. You can get a free VRAM from [here](https://vast.ai/)
We recommend 4-8GB of VRAM for this project. 
Mistral 7B and llama3.1 8B are the recommended models for this project.
Ensure ollamas is installed on your machine and running before running this project. You can install ollamas from [here](ollama.com)

## File structure
.   
├── Makefile - This file contains the commands to run the project.   
├── README.md - This file contains the project documentation. This is the file you are currently reading.     
├── requirements.txt - This file contains the dependencies for the project.   
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

## Usage
This project uses LLMs to send airtime to a phone number. The difference is that we are going to use the Africa's Talking API to send airtime to a phone number using Natural language. Here are examples of prompts you can use to send airtime to a phone number:
- Send airtime to xxxxxxxxxx046 and xxxxxxxxxx524 with an amount of 10 in currency KES
- Send a message to xxxxxxxxxx046 and xxxxxxxxxx524 with a message "Hello, how are you?", using the username "username".


## Contributing
Contributions are welcome. If you would like to contribute to the project, you can fork the repository, create a new branch, make your changes and then create a pull request.

## License
[License information](https://github.com/Shuyib/tool_calling_api/blob/main/LICENSE).
