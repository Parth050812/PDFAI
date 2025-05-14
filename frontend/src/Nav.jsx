import React, { useRef, useState, useEffect } from "react";
import './Nav.css';
import head from "/head.png";
function Nav({ selectedFile, setSelectedFile }) {
  const fileInputRef = useRef();
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchUploadedFiles = async (file=null) => {
    try {
      const res = await fetch("http://localhost:8000/pdfs", {
        method: "GET",
      });
      const data = await res.json(); 
      setUploadedFiles(data);
      if (data.length > 0) {
        if(file && data.includes(file)){
          setSelectedFile(file);
        }
        else{
        setSelectedFile(data[0]);
        }
      }
    } catch (err) {
      console.error("Failed to fetch uploaded files:", err);
    }
  };

  useEffect(() => {
    fetchUploadedFiles();
  }, []);

  const handleButtonClick = () => {
    fileInputRef.current.click(); 
  };

  const handleFileChange = async (e) => {
    setLoading(true);
    const file = e.target.files[0];
    if (file) {
      const formData = new FormData();
      formData.append("file", file);
      try {
        const res = await fetch("http://localhost:8000/upload", {
          method: "POST",
          body: formData,
        });

        const data = await res.json();
        console.log("Upload successful:", data.filename);
        fetchUploadedFiles(file.name);
      } catch (err) {
        console.error("Upload failed:", err);
      }finally{
        setLoading(false);
      }
    }
  };


  return (
    <>
      <div className="Nav-header">
        <div className="naam"><img className="photu" src={head} alt="aiplanet" style={{ width: "110px", height: "40px" }} /></div>
        <div className="but">
        { uploadedFiles.length>0 ? (
            <select
              value={selectedFile}
              onChange={(e) => setSelectedFile(e.target.value)}
              className="green-text-border"
            > 
              {uploadedFiles.map((name, index) => (
                <option key={index} value={name}>
                  {name}
                </option>

              ))}
            </select>) :
          (<div></div>)
          }
          <button onClick={handleButtonClick}>{loading ? "Uploading":"Upload Pdf"}</button>
          <input
            type="file"
            accept="application/pdf"
            ref={fileInputRef}
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
        </div>
      </div>
    </>
  );
}

export default Nav;
