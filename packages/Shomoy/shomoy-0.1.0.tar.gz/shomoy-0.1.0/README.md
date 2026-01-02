<div align="center">

# Shomoy <br>

### A time capsule for your terminal.
</div>

## Installation
Installing the program is very easy. Simply clone the repository or download main.py.

There you have it!

## Building
This program is dependant on [Rich](https://github.com/Textualize/rich?tab=readme-ov-file), [Cryptography](https://github.com/pyca/cryptography), [TinyDB](https://github.com/msiemens/tinydb). To build the program, you need to use Pyinstaller or a compiler of your choice:
```
pip install pyinstaller
```

To compile using Pyinstaller, run this:

```bash
$ pyinstaller --onefile main.py
```

Finally, Your build will be located in: `Shomoy\dist\`

<br>

## Running

Once the build is complete, you can simply open the file or run it through your terminal in the build directory and type:

```bash
$ .\main.exe (Change the main.exe to your build file)
```
Or if you want to use the main.py instead:
```
$ python main.py
```


<br>

## Contribution
Contributing to Tale is simple. You have to fork the repository and clone it. Make your changes. After you are done, just push the changes to your fork and make a pull request. 

I hope that you will be making some amazing changes!

<br>

## License

Licensed under the [MIT License](./LICENSE).
