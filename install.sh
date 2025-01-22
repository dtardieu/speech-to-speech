git clone --single-branch --branch pulso-chat git@github.com:dtardieu/speech-to-speech.git

/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
echo >> /Users/dtardieu/.zprofile
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> /Users/
eval "$(/opt/homebrew/bin/brew shellenv)"

brew install python@3.12
brew install virtualenv
brew install rust
brew install mecab


git submodule init
git submodule update

virtualenv venv
source venv/bin/activate

pip install -r requirements_mac.txt
pip install -r pulsochat/requirements.txt

pip install python-osc

echo 'export OPENAI_API_KEY=YOUR_KEY' >> ~/.zshenv

python -m unidic download
