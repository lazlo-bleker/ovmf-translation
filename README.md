# Speech Translation with Azure Cognitive Services

This project offers a Python-based live speech translation tool. It was designed for live English translations of German lectures at the Oskar von Miller Forum. The translation service utilizes the Azure Cognitive Services Speech SDK.

## How It Works

The project contains two main components: a `SpeechTranslator` class and a script that uses this class to perform live translation. The `SpeechTranslator` class takes care of setting up the translation services using the provided API key and region, translating recognized speech, and handling translation events.

Once an instance of the `SpeechTranslator` class is created in the script, the `translate_speech` method can be called to start the translation process. The live audio is picked up, translated from German to English, and the translation is synthesized into audible English speech.

## Prerequisites

To use this tool, you will need:

- Python 3.6 or later.
- Azure Cognitive Services Speech SDK for Python installed 
```bash
pip install azure-cognitiveservices-speech
```

## Set up Azure Cognitive Services

Create an Azure account if you do not already have one. Visit the [Azure portal](https://portal.azure.com/) to create an account.
Once you have an Azure account, you need to create a resource for Speech Services. Follow the steps in this guide: [Create a resource](https://docs.microsoft.com/azure/cognitive-services/cognitive-services-apis-create-account?tabs=multiservice%2Cwindows#create-a-resource).
Once the Speech Services resource is created, you can find the API key in the Azure portal. Navigate to your resource and find the Keys and Endpoint page under Resource Management.
Replace `your_api_key` with the API key you obtained from the Azure portal in `run_translation.py`.

## Setting up Audio Input Source

Before running the program, you need to set the lecture audio as the audio input source for your operating system. Make sure that the audio input is set to the device or system capturing the lecture audio.

## Streaming the Translated Audio

To stream the translated audio to an audience, we recommend using a virtual audio routing tool that can route the system audio (which includes the translated speech) to a virtual microphone. This virtual microphone can then be set as the audio source in your streaming platform.

For macOS users, we recommend [BlackHole](https://existential.audio/blackhole/), an open-source virtual audio driver. For Windows users, [VB-Cable](https://vb-audio.com/Cable/) is a great option.

Once the virtual audio routing tool is set up, start a Zoom meeting (or any other streaming platform), go to the audio settings, and select the virtual audio device as the microphone.

## Running the Translation

To start the translation, run the `run_translation.py` script. This will initiate the translation process, which will continue until you stop it.

Please note that this tool is designed for translating live German lectures to English. If you want to translate a different source language or to a different target language, you need to modify the source and target language parameters when creating an instance of the `SpeechTranslator` class.

## Limitations

This tool uses Azure's real-time speech translation service, which has a delay between speech recognition and output of translated speech. This is inherent to the design of Azure's service and may vary based on speaker and their speech pattern (e.g. frequency of pauses in speech). In general, there is an expected delay of up to a 30 seconds for translation.

## Contributing

Contributions to improve the tool are welcome. Please feel free to submit issues and pull requests.
