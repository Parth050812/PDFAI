import { useState } from 'react'
import './App.css'
import Nav from './Nav';
import Container from './Container';
import Backendstatus from './Backendstatus';

function App() {
  const [selectedFile, setSelectedFile] = useState('');

  return (
    <>
      <div className="bruh">
      <Backendstatus/>
      <Nav selectedFile={selectedFile} setSelectedFile={setSelectedFile}/>
      <Container selectedFile={selectedFile}/>
      </div>
    </>
  )
}

export default App