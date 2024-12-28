import React, { useState } from "react";
import axios from "axios";

function App() {
    const [file, setFile] = useState(null);
    const [format, setFormat] = useState("mp4");
    const [status, setStatus] = useState("");
    const [fileId, setFileId] = useState("");

    const handleFileChange = (e) => setFile(e.target.files[0]);
    const handleFormatChange = (e) => setFormat(e.target.value);

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!file) {
            alert("Please select a file to upload.");
            return;
        }

        const formData = new FormData();
        formData.append("file", file);
        formData.append("format", format);

        setStatus("Uploading...");
        try {
            const response = await axios.post(
                `${import.meta.env.VITE_API_URL}/submit`,
                formData
            );
            setStatus("Processing...");
            checkStatus(response.data.video_id);
        } catch (error) {
            setStatus(`Error: ${error.response?.data?.error || error.message}`);
        }
    };

    const checkStatus = async (videoId) => {
        const interval = setInterval(async () => {
            try {
                const response = await axios.get(
                    `${import.meta.env.VITE_API_URL}/status/${videoId}`
                );
                const { status, output_file, video_id } = response.data;
                console.log(response.data);
                if (status === "completed") {
                    setStatus("Completed!");
                    setFileId(video_id);
                    clearInterval(interval);
                }
            } catch (error) {
                console.error(error);
                clearInterval(interval);
            }
        }, 2000);
    };

    return (
        <div>
            <h1>Video Converter</h1>
            <form onSubmit={handleSubmit}>
                <input type="file" onChange={handleFileChange} />
                <select value={format} onChange={handleFormatChange}>
                    <option value="mp4">MP4</option>
                    <option value="avi">AVI</option>
                </select>
                <button type="submit">Upload</button>
            </form>
            <p>Status: {status}</p>
            {fileId && (
                <a
                href={`${import.meta.env.VITE_API_URL}/download/${fileId.replace(/\.[^.]+$/, '')}.${format}`}
                download
                >
                    Download
                </a>
            )}
        </div>
    );
}

export default App;
