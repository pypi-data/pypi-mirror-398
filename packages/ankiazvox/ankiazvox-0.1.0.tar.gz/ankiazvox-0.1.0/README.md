# **ankiazvox**

**ankiazvox** is a professional CLI tool designed to synchronize Anki notes with high-quality neural audio powered by Azure Cognitive Services. It automates the process of fetching text, generating speech, and updating your Anki cards.

## **✨ Features**

* **Neural TTS**: Uses Azure's state-of-the-art Neural voices for natural, human-like speech.  
* **Seamless Integration**: Automatically uploads audio to Anki's media folder and updates the \[sound:...\] tags via AnkiConnect.  
* **Batch Processing**: Efficiently processes multiple notes using a single query.  
* **Flexible CLI**: Built with Click for a smooth command-line experience and tqdm for real-time progress tracking.  
* **Smart Querying**: Supports the full range of Anki's search syntax.

## **🚀 Installation**

### **1\. Prerequisites**

* **Anki Desktop** with the [AnkiConnect](https://ankiweb.net/shared/info/2055492159) add-on installed.  
* An **Azure Speech Service** subscription (Key and Region).

### **2\. Install from Source**

Clone the repository and install the dependencies:

git clone \[https://github.com/ericxu131/ankiazvox.git\](https://github.com/ericxu131/ankiazvox.git)  
cd ankiazvox  
pip install .

## **⚙️ Configuration**

Create a .env file in the project root directory with your credentials:

\# AnkiConnect Settings  
ANKI\_CONNECT\_URL=\[http://127.0.0.1:8765\](http://127.0.0.1:8765)

\# Azure Speech Settings  
AZURE\_SPEECH\_KEY=your\_azure\_api\_key  
AZURE\_SPEECH\_REGION=your\_service\_region (e.g., eastus)

\# Default Voice Configuration  
DEFAULT\_VOICE=en-US-AvaMultilingualNeural

## **🛠 Usage**

After installation, you can use the azv (alias) or ankiazvox command.

### **Basic Sync**

Sync notes from a specific deck using default settings:

azv sync \--query "deck:MyEnglishDeck" \--source "Front" \--target "AudioField"

### **Advanced Usage**

Override the default voice and limit the number of notes for a test run:

azv sync \-q "tag:new\_words" \-s "Word" \-t "Pronunciation" \-v "zh-CN-YunyangNeural" \--limit 10

### **Options**

| Option | Short | Description |  
| \--query | \-q | Anki search query (e.g., deck:Default, tag:marked) |  
| \--source | \-s | The field name containing the text to be synthesized |  
| \--target | \-t | The field name where the \[sound:...\] tag will be stored |  
| \--voice | \-v | Overrides the default Azure voice defined in .env |  
| \--limit | | Max number of notes to process in this run |  
| \--temp-dir | | Custom directory for temporary audio files |

## **🤝 Contributing**

Contributions are welcome\! Please feel free to submit a Pull Request.

1. Fork the Project  
2. Create your Feature Branch (git checkout \-b feature/AmazingFeature)  
3. Commit your Changes (git commit \-m 'Add some AmazingFeature')  
4. Push to the Branch (git push origin feature/AmazingFeature)  
5. Open a Pull Request

## **📄 License**

Distributed under the **MIT License**. See LICENSE for more information.

## **👤 Author**

**Eric Xu** \- [xulihua2006@gmail.com](mailto:xulihua2006@gmail.com)

Project Link: [https://github.com/ericxu131/ankiazvox](https://www.google.com/search?q=https://github.com/ericxu131/ankiazvox)