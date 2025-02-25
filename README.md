# All below information is from the original which can be found at danielbonkowsky/subwaysurfers-text please give the original creator some love if you find this usefull. Thank you danielbonkowsky/subwaysurfers-text

# Text to Tracks: A Subway Surfers Video Article Converter

## Inspiration
Maintaining focus and attention while reading educational articles can be challenging. We recognized this issue and aimed to provide a solution that makes learning more engaging.

## What it does
Our web application takes a link to an article, scrapes the text, and puts it in the TikTok Subway Surfers-style video. This format is highly engaging which enables users to pay attention to the content and absorb information effectively.

## How we built it
We used Python, HTML/CSS, Flask, OpenCV, goose3, Vosk API, and various other python libraries.

## Supported platforms

We tested our code on MacOS. 

The local server should work on Safari, Chrome, and Firefox browsers. 


## Installation

1. Install [Python](https://www.python.org/) (>= 3.11)

2. Clone our repository. 
   ```
   git clone https://github.com/danielbonkowsky/subwaysurfers-text.git
   ```

3. Install `pip3` dependencies
   ```
   pip3 install -r requirements-pip.txt
   ```

4. Install `brew` dependencies:
   ```
   xargs brew install < requirements-brew.txt
   ```

5. Download the Subway Surfers [background gameplay](https://drive.google.com/file/d/1ZyFZKIB1HiZM_XDQPRRiiAIvU4sgl10k/view?usp=drive_link), title it `surf.mp4` and place it in the `static` folder of your local repository. 

6. Download the [Vosk English Model](https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip), unzip the folder and place it in the `static` folder of your local repository.


## Running the Server

1. Navigate into the repository in your terminal.

2. Create the development server. 
   ```
   flask run
   ```

3. Open the local server in your browser. 

4. Paste a link to the article you want converted into the textbox, and press `<enter>`! The video takes a while to generate, but the terminal should show that the program is running.
   * If it asks you to override any files, override them. 

