
---  

<div align="center">
  <img src="./media/clinkey_green_title.svg" alt="ClinKey" style="max-width: 80%; margin: -40px auto;"/>
</div>
  
![GitHub License](https://img.shields.io/github/license/dim-gggl/Clinkey?style=plastic)
![PyPI - Version](https://img.shields.io/pypi/v/clinkey-cli?style=plastic&logo=python&logoColor=yellow)
![GitHub Release Date](https://img.shields.io/github/release-date/dim-gggl/clinkey-cli?style=plastic&logo=github&logoColor=green)


Your _**SECRET BUDDY**_, assisting you in crafting strong passwords you can actually remember.

## Installation

The easiest way is to use `pip` (recommended for CLI tools) or `pipx`. 

```bash
pip install clinkey-cli
# or
pipx install clinkey-cli
# or 
uv add clinkey-cli
# or
uv pip install clinkey-cli
```

For macOS users, you can also use Homebrew:
- Replace <user>/<repo> with the actual tap path  

```bash
brew tap dim-gggl/clinkey-cli
brew install clinkey-cli
```

## ✨ Usage
`clinkey` works in two ways: 
- Interactive Mode (cool and guided).
	> Run `clinkey` with no arguments to launch the guided interface. It's the best way to get started !
- Direct Mode (fast and efficient).
	> Use flags to get what you want in a single line.

### The parameters

#### The types (`-t` | `--type`)  
  
There are 3 different types of clinkey passwords : 
- `normal` : set by default. Containing only letters. flag : `-t` | `--type normal`
- `strong` : like `normal`, but with digits. flag : `-t` | `--type strong`
- `super_strong` : like `strong`, but with special characters. flag : `-t` | `--type super_strong`.

> Note that in interactive mode, as well as in the [web interface](https://dim-gggl.github.io/ClinKey/), `normal` is called `Vanilla`, `strong` is called `Twisted` and `super_strong` is called `So NAAASTY` or `Super Twisted`.  
  
#### The length (`-l` | `--length`)  
    
The length of your password is set by default to 16 characters. You can change it by using the `-l` | `--length` flag. from 1 to 10000... characters.  

#### The number of passwords (`-n` | `--number`)  
   
It is possible to generate multiple passwords at once by using the `-n` | `--number` flag. from 1 to 10000... passwords.  **WARNING** : if you don"t want your CPU to explode, don't generate more than 500 passwords at once.  

#### The separator (`-ns` | `--no-sep`)  
  
The pattern of passwords that `clinkey` uses hyphen and underscore as separators by default to make the whole result pronounceable. You can change it by using the `-ns` | `--no-sep` flag.  

#### The lowercase (`-low` | `--lower`)  
  
By default `clinkey` generates passwords in uppercase. You can change it by using the `-low` | `--lower` flag.  

#### The output (`-o` | `--output`)  
  
Eventually, you can save the result to a file and avoid echoing it to the terminal by using the `-o` | `--output` flag followed by the path to the file.  

