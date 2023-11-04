import azure.cognitiveservices.speech as speechsdk
import time
import json
import os
import datetime


class SpeechTranslator:
    base_synth_time = 1.35712551
    per_char_synth_time = 0.05745246
    """Class for live speech to speech translation."""
    def __init__(self, api_key: str, region: str = 'westeurope', source_language: str = 'de-DE',
                 target_language: str = 'en', intermediate_translations: bool = True, verbose: bool = True):
        self.api_key = api_key
        self.region = region
        self.source_language = source_language
        self.target_language = target_language
        self.intermediate_translations = intermediate_translations
        self.verbose = verbose
        self.done = False
        self.last_synthesized_index = 0  # To keep track of the last index of the last synthesized text
        self.intermediate_buffer = ["", "", ""]  # Buffer for storing the 3 most recent intermediate translations
        self.synthesized_text = ""  # Stores cumulative intermediate translations
        self.speech_queue = []
        self.last_synth_time = float('nan') # Time of last speech synthesis completion
        self.last_recognized_time = time.time() # Time of last intermediate or final speech recognition

        self.pr = 0
        if os.path.exists(f'speech_data_pr{self.pr}.json'):
            with open(f'speech_data_pr{self.pr}.json', 'r') as f:
                self.speech_data = json.load(f)
        else:
            self.speech_data = {'prosody rate': self.pr, 'num_chars': [], 'time_per_char': []}


    def translate_speech(self):
        """Main method to initiate live speech translation. Audio in is taken from the operating system audio input."""
        # Configure and create speech synthesizer and translation recognizer
        translation_config = speechsdk.translation.SpeechTranslationConfig(
            subscription=self.api_key, region=self.region)
        speech_config = speechsdk.SpeechConfig(subscription=self.api_key, region=self.region)
        translation_config.speech_recognition_language = self.source_language
        translation_config.add_target_language(self.target_language)
        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
        recognizer = speechsdk.translation.TranslationRecognizer(translation_config=translation_config)

        # Connect callback methods to the appropriate events
        recognizer.session_stopped.connect(self._stop_cb)
        recognizer.recognized.connect(lambda evt: self._recognized_cb(evt, speech_synthesizer))
        if self.intermediate_translations:
            recognizer.recognizing.connect(lambda evt: self._recognizing_cb(evt, speech_synthesizer))
        speech_synthesizer.synthesis_completed.connect(lambda evt: self._synthesis_completed_cb(evt))
        speech_synthesizer.synthesis_started.connect(lambda evt: self._synthesis_started_cb(evt))

        # Start translation until interrupted
        recognizer.start_continuous_recognition()
        try:
            while not self.done:
                pass
        except KeyboardInterrupt:
            with open(f'speech_data_pr{self.pr}.json', 'w') as f:
                json.dump(self.speech_data, f)
            recognizer.stop_continuous_recognition()

    def _stop_cb(self, evt):
        """Callback method for when the translation session stops."""
        self._log('Translation stopped')
        self.done = True

    def _recognized_cb(self, evt, speech_synthesizer):
        """Callback method for when a phrase has been fully recognized and translated."""
        if evt.result.reason == speechsdk.ResultReason.TranslatedSpeech:
            translation = evt.result.translations[self.target_language]

            # Compare cumulative intermediate translations with the final translation
            if self.synthesized_text == translation[:len(self.synthesized_text)]:
                ok = 'OK'
            else:
                ok = 'ERROR'

            self._log(f'Final translation ({ok}): {translation}')
            text_to_synthesize = evt.result.translations[self.target_language][self.last_synthesized_index:]
            self.last_synthesized_index = 0  # Reset the last synthesized text index
            self.synthesized_text = ""  # Reset cumulative intermediate translations
            self.last_recognized_time = time.time()
            self._synthesize_text(text_to_synthesize, speech_synthesizer)

    def _recognizing_cb(self, evt, speech_synthesizer):
        """Callback method for when speech is being recognized and translated."""
        self._log(f'Delay: {str(datetime.timedelta(seconds=int(self._speech_queue_time() + 0.5)))}')
        if evt.result.reason == speechsdk.ResultReason.TranslatingSpeech:
            # Update the intermediate translation buffer with the latest translation
            self.intermediate_buffer.pop(0)
            self.intermediate_buffer.append(evt.result.translations[self.target_language])

            # If all buffer entries contain ". ", proceed with equality check
            if all(". " in text for text in self.intermediate_buffer):
                up_to_dot = [text[:text.rindex(". ") + 1] for text in self.intermediate_buffer]

                # If all buffer entries are the same up to the last ". ", proceed with synthesis
                if up_to_dot[0] == up_to_dot[1] == up_to_dot[2]:
                    text_to_synthesize = up_to_dot[0][self.last_synthesized_index:]
                    self.last_synthesized_index = len(up_to_dot[0])  # Update the last synthesized text index

                    # If there is text to synthesize, log it and synthesize it
                    if len(text_to_synthesize) > 0:
                        self._log(f'Intermediate translation: {text_to_synthesize}')
                        self.synthesized_text += text_to_synthesize  # Update the until now synthesized text
                        self.last_recognized_time = time.time()
                        self._synthesize_text(text_to_synthesize, speech_synthesizer)

    def _synthesis_started_cb(self, evt):
        self.last_synth_time = time.time()

    def _synthesis_completed_cb(self, evt):
        time_to_complete = time.time() - self.last_synth_time
        self.speech_data['num_chars'].append(self.speech_queue[0])
        self.speech_data['time_per_char'].append(time_to_complete/self.speech_queue[0])
        self.speech_queue.pop(0)

    def _synthesize_text(self, text, speech_synthesizer):
        """Method to synthesize text into speech"""
        ssml_text = (
            "<speak version='1.0' xmlns='https://www.w3.org/2001/10/synthesis' "
            "xmlns:mstts='https://www.w3.org/2001/mstts' xml:lang='en-US'>"
            "<voice name='en-US-JennyNeural'>"
            f"<prosody rate='+{self.pr}%'>"
            "<mstts:express-as style='default'>"
            f"{text}"
            "</mstts:express-as>"
            "</prosody>"
            "</voice>"
            "</speak>")
        self.speech_queue.append(len(text))
        self._log(f'speech_queue = {self.speech_queue}')
        speech_synthesizer.speak_ssml_async(ssml_text)

    def _speech_queue_time(self):
        speech_queue_times = [self.per_char_synth_time*item + self.base_synth_time for item in self.speech_queue]
        current_speech_time = time.time() - self.last_recognized_time
        current_synth_time = time.time() - self.last_synth_time if self.speech_queue != [] else 0
        speech_queue_time = sum(speech_queue_times) + current_speech_time - current_synth_time
        return speech_queue_time

    def _log(self, message):
        if self.verbose:
            print(message)
