import React, { useEffect, useState } from "react";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import ReactMarkdown from "react-markdown";
import "./Container.css";

function Container({ selectedFile }) {
  const [text, setText] = useState("");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // Auto-resize textarea for user typing
  const handleInput = (e) => {
    const textarea = e.target;
    textarea.style.height = "auto";
    textarea.style.height = `${textarea.scrollHeight}px`;
    setText(textarea.value);
  };

  // Reset chat history and post info message whenever selected document changes
  useEffect(() => {
    if (selectedFile) {
      setMessages([
        {
          type: "info",
          content: `**Ask any question from " \`${selectedFile}\` "**`,
        },
      ]);
    }
  }, [selectedFile]);

  // Format existing messages to backend chat history standard
  const getFormattedHistory = () => {
    return messages
      .filter((msg) => msg.type === "user" || msg.type === "ai")
      .map((msg) => ({
        role: msg.type === "user" ? "user" : "assistant",
        content: msg.content,
      }));
  };

  const handleSubmit = async () => {
    if (text.trim() === "") return;

    const userText = text;
    const userMessage = { type: "user", content: userText };
    
    // Prepare history snapshot before state update
    const historyPayload = getFormattedHistory();

    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setText("");
    setIsLoading(true);

    try {
      if (!selectedFile) {
        throw new Error("Please select a file first");
      }
      const url = "https://pdfai-backend-h0cb.onrender.com";
      //const url = "http://127.0.0.1:8000";
      const ask = url + "/ask";
      const res = await fetch(ask, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          filename: selectedFile,
          question: userText,
            history: historyPayload, // Correctly mapped chat history payload
        }),
      });

      if (!res.ok) {
        throw new Error("Failed to get response from server");
      }

      const data = await res.json();
      let formattedAnswer = data.answer;
      formattedAnswer = data.answer
        .replace(/\*\s+\*\*/g, "* **")
        .replace(/\n{2,}/g, "\n");

      setMessages((prevMessages) => [
        ...prevMessages,
        { type: "ai", content: formattedAnswer },
      ]);
    } catch (error) {
      setMessages((prevMessages) => [
        ...prevMessages,
        { type: "error", content: error.message },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="con">
      <div className="content">
        {messages.map((msg, index) =>
          msg.type === "user" ? (
            <div key={index} className="message-row">
              <div className="message">{msg.content}</div>
            </div>
          ) : msg.type === "ai" ? (
            <div key={index} className="ai-message-row">
              <div className="ai-message">
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>
            </div>
          ) : (
            <div key={index} className="pdf-message-row">
              <div className="pdf-message">
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>
            </div>
          )
        )}
        {isLoading && (
          <div className="ai-message-row">
            <div className="ai-message">Thinking...</div>
          </div>
        )}
      </div>
      <div className="input">
        <textarea
          value={text}
          onInput={handleInput}
          onKeyDown={handleKeyPress}
          placeholder="Send a Message ..."
          disabled={isLoading}
        ></textarea>
        <button
          id="bh"
          onClick={handleSubmit}
          disabled={isLoading || text.trim() === ""}
        >
          <ArrowForwardIcon />
        </button>
      </div>
    </div>
  );
}

export default Container;