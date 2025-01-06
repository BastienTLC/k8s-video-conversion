import React, { useState, useRef } from 'react';
import { FileUpload } from 'primereact/fileupload';
import { Dropdown } from 'primereact/dropdown';
import { ProgressSpinner } from 'primereact/progressspinner';
import { Button } from 'primereact/button';
import { Card } from 'primereact/card';
import { Toast } from 'primereact/toast';
import axios from 'axios';

import 'primereact/resources/themes/lara-light-indigo/theme.css';
import 'primereact/resources/primereact.min.css';
import 'primeicons/primeicons.css';
import 'primeflex/primeflex.css';

const App = () => {
    const [file, setFile] = useState(null);
    const [format, setFormat] = useState('');  // Changed to string instead of object
    const [status, setStatus] = useState("");
    const [fileId, setFileId] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const toast = useRef(null);
    const fileUploadRef = useRef(null);

    const formatOptions = [
        { label: 'MP4', value: 'mp4' },
        { label: 'AVI', value: 'avi' },
        { label: 'MOV', value: 'mov' },
        { label: 'M4V', value: 'm4v' },
        { label: 'MKV', value: 'mkv' },
        { label: 'FLV', value: 'flv' },
        { label: 'WMV', value: 'wmv' },
        { label: 'WEBM', value: 'webm' }
    ];

    const onFileSelect = (e) => {
        if (e.files && e.files[0]) {
            setFile(e.files[0]);
            toast.current.show({
                severity: 'info',
                summary: 'File Selected',
                detail: `${e.files[0].name} ready for conversion`
            });
        }
    };

    const onFileRemove = () => {
        setFile(null);
        setFileId("");
        setStatus("");
    };

    const checkStatus = async (videoId) => {
        try {
            const response = await axios.get(
                `${import.meta.env.VITE_API_URL}/status/${videoId}`
            );
            const { status, video_id } = response.data;

            if (status === "completed") {
                setStatus("completed");
                setFileId(video_id);
                setIsLoading(false);
                toast.current.show({
                    severity: 'success',
                    summary: 'Conversion Complete',
                    detail: 'Your video is ready for download'
                });
            } else if (status === "processing") {
                setTimeout(() => checkStatus(videoId), 2000);
            }
        } catch (error) {
            console.error(error);
            setIsLoading(false);
            toast.current.show({
                severity: 'error',
                summary: 'Error',
                detail: 'Failed to check conversion status'
            });
        }
    };

    const handleConvert = async () => {
        if (!file || !format) {
            toast.current.show({
                severity: 'warn',
                summary: 'Warning',
                detail: 'Please select both file and format'
            });
            return;
        }

        setIsLoading(true);
        const formData = new FormData();
        formData.append("file", file);
        formData.append("format", format);  // Now format is directly the string value

        try {
            const response = await axios.post(
                `${import.meta.env.VITE_API_URL}/submit`,
                formData
            );
            setStatus("processing");
            checkStatus(response.data.video_id);
        } catch (error) {
            setIsLoading(false);
            toast.current.show({
                severity: 'error',
                summary: 'Upload Failed',
                detail: error.response?.data?.error || error.message
            });
        }
    };

    const header = (
        <div className="flex align-items-center gap-2">
            <i className="pi pi-video text-xl"></i>
            <span className="text-xl font-bold">Video Converter</span>
        </div>
    );

    return (
        <div className="flex align-items-center justify-content-center min-h-screen bg-gray-100 p-4">
            <Toast ref={toast} />
            <Card header={header} className="w-full max-w-lg">
                <div className="flex flex-column gap-4">
                    <FileUpload
                        ref={fileUploadRef}
                        mode="advanced"
                        accept="video/*"
                        maxFileSize={100000000}
                        customUpload
                        auto
                        chooseLabel="Select Video"
                        uploadLabel="Convert"
                        onSelect={onFileSelect}
                        onClear={onFileRemove}
                        emptyTemplate={
                            <div className="flex flex-column align-items-center p-5">
                                <i className="pi pi-cloud-upload text-5xl mb-3"></i>
                                <span>Drag and drop your video here</span>
                            </div>
                        }
                    />

                    <Dropdown
                        value={format}
                        onChange={(e) => setFormat(e.value)}  // This now sets just the string value
                        options={formatOptions}
                        placeholder="Select Output Format"
                        className="w-full"
                    />

                    <Button
                        label="Convert Video"
                        icon="pi pi-cog"
                        onClick={handleConvert}
                        disabled={!file || !format || isLoading}
                        loading={isLoading}
                    />

                    {isLoading && (
                        <div className="flex flex-column align-items-center gap-2">
                            <ProgressSpinner
                                style={{width: '50px', height: '50px'}}
                                strokeWidth="4"
                            />
                            <span className="text-sm">Converting your video...</span>
                        </div>
                    )}

                    {status === "completed" && fileId && (
                        <Button
                            label="Download Converted Video"
                            icon="pi pi-download"
                            severity="success"
                            onClick={() => {
                                window.location.href = `${import.meta.env.VITE_API_URL}/download/${fileId.replace(/\.[^.]+$/, '')}.${format}`;
                            }}
                        />
                    )}
                </div>
            </Card>
        </div>
    );
};

export default App;