import { useEffect, useRef, useState } from "react";

const SpeechRecognitionAPI =
  typeof window !== "undefined" &&
  (window.SpeechRecognition || window.webkitSpeechRecognition);

export default function VoiceButton({ onResult, onError, disabled }) {
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef(null);

  useEffect(() => {
    if (!SpeechRecognitionAPI) return;
    const recognition = new SpeechRecognitionAPI();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      onResult(transcript);
    };
    recognition.onerror = (event) => {
      onError(event.error === "no-speech" ? "Didn't catch that — try again." : `Mic error: ${event.error}`);
      setListening(false);
    };
    recognition.onend = () => setListening(false);

    recognitionRef.current = recognition;
  }, [onResult, onError]);

  const toggleListening = () => {
    if (!SpeechRecognitionAPI) {
      onError("Voice input isn't supported in this browser — try Chrome, or type your command below.");
      return;
    }
    if (listening) {
      recognitionRef.current.stop();
      setListening(false);
    } else {
      try {
        recognitionRef.current.start();
        setListening(true);
      } catch (e) {
        onError("Couldn't access the microphone. Check your browser permissions.");
      }
    }
  };

  return (
    <button
      onClick={toggleListening}
      disabled={disabled}
      className={`relative flex h-24 w-24 items-center justify-center rounded-full text-white shadow-lg transition-transform
        ${listening ? "mic-pulse scale-105" : "hover:scale-105"}
        disabled:opacity-50 disabled:cursor-not-allowed`}
      style={{
        background: listening
          ? "linear-gradient(135deg, #e85d75, #cf3f59)"
          : "linear-gradient(135deg, #1c8a75, #0b5449)",
      }}
      aria-label={listening ? "Stop listening" : "Start voice command"}
    >
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-9 w-9">
        <path d="M12 15a3 3 0 003-3V6a3 3 0 10-6 0v6a3 3 0 003 3z" />
        <path d="M19 11a1 1 0 10-2 0 5 5 0 01-10 0 1 1 0 10-2 0 7 7 0 006 6.93V20H9a1 1 0 100 2h6a1 1 0 100-2h-2v-2.07A7 7 0 0019 11z" />
      </svg>
    </button>
  );
}