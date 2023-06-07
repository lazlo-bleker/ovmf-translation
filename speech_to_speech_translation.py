import azure.cognitiveservices.speech as speechsdk

API_KEY = '205881039a6c416783b9bb6397ca6f0e'
ENDPOINT = 'https://westeurope.api.cognitive.microsoft.com/sts/v1.0/issuetoken'

def translate_speech():
    # Creates an instance of a speech translation config with specified subscription key and endpoint.
    translation_config = speechsdk.translation.SpeechTranslationConfig(
        subscription=API_KEY, endpoint=ENDPOINT)

    # Sets source and target languages.
    translation_config.speech_recognition_language = 'de-DE'
    translation_config.add_target_language('en')

    # Translate text to speech
    speech_config = speechsdk.SpeechConfig(subscription=API_KEY, endpoint=ENDPOINT)
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)

    # Creates a translation recognizer using and audio configuration
    recognizer = speechsdk.translation.TranslationRecognizer(translation_config=translation_config)

    # Prepare event handlers
    done = False

    def stop_cb(evt):
        """callback that stops continuous recognition upon receiving an event `evt`"""
        print('CLOSING on {}'.format(evt))
        nonlocal done
        done = True

    def recognized_cb(evt):
        """callback that handles the `recognized` event"""
        if evt.result.reason == speechsdk.ResultReason.TranslatedSpeech:
            print('Recognized: {}'.format(evt.result.text))
            print('Translated into English: {}'.format(evt.result.translations['en']))

    def recognizing_cb(evt):
        """callback that handles the `recognizing` event"""
        print('Recognizing: {}'.format(evt.result.text))

    recognizer.recognizing.connect(recognizing_cb)  # <<< NEW LINE HERE
    recognizer.recognized.connect(recognized_cb)
    recognizer.session_stopped.connect(stop_cb)

    # Start continuous recognition
    recognizer.start_continuous_recognition()

    # Keep the program running while recognition is occurring
    while not done:
        pass

    # Stop continuous recognition
    recognizer.stop_continuous_recognition()

translate_speech()
