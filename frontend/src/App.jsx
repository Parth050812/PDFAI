import { useState } from 'react'
import './App.css'
import Nav from './Nav';
import Container from './Container';

function App() {
  const [selectedFile, setSelectedFile] = useState('');

  return (
    <>
      <div className="bruh">
      <Nav selectedFile={selectedFile} setSelectedFile={setSelectedFile}/>
      <Container selectedFile={selectedFile}/>
      </div>
    </>
  )
}

export default App
