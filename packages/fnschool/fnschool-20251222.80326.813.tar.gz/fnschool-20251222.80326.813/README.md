
<hr/>
<div align="center">
    <pre>
 _____ _   _ ____   ____ _   _  ___   ___  _     
|  ___| \ | / ___| / ___| | | |/ _ \ / _ \| |    
| |_  |  \| \___ \| |   | |_| | | | | | | | |    
|  _| | |\  |___) | |___|  _  | |_| | |_| | |___ 
|_|   |_| \_|____/ \____|_| |_|\___/ \___/|_____|
    </pre>
</div>
<p align="center">
    funingschool
</p>
<h4 align="center">
    NO Just some simple scripts for warehousing and consuming.
</h4>
<hr/>
<p align="center">
    <a href="https://gitee.com/larryw3i/funingschool/blob/master/Documentation/README/zh_CN.md">简体中文</a> •
    <a href="https://github.com/larryw3i/funingschool/blob/master/README.md">English</a>
</p>

<p align="center">
    <a href="#key-features">
        Key Features
    </a>
    •
    <a href="#how-to-use">
        How To Use
    </a>
    •
    <a href="#credits">
        Credits
    </a>
    •
    <a href="#support">
        Support
    </a>
    •
    <a href="#license">
        License
    </a>
</p>

![Screenshot](https://raw.githubusercontent.com/larryw3i/funingschool/master/Documentation/images/44e58998-da32-11f0-b726-700894a38a35.png)

<h2 id="key-features">
    Key Features
</h2>

<h3>
    warehousing and consuming
</h3>

* Read food spreadsheets automatically.
* The simplest and most straightforward `consuming sheets`.
* Update sheets (warehousing, consuming, summing, etc) automatically.
* Reduce calculation errors.
* Effectively eliminate unit prices containing infinite decimals.
* Merge food sheets between spreadsheets.  
* Easy to use.

<h2 id="how-to-use">
    How To Use
</h2>

<h3>
    Install Python3
</h3>
<p>

on `Debian`:

```bash
sudo apt-get install python3 python3-pip
```  
For `Windows 10` and `Windows 11`, you can install Python3 from https://www.python.org/getit/ . (`fnschool` requires Python 3.12 or later)
</p>

<h3>
    Install fnschool and run it
</h3>

<p>

Run the command line application:
* `Debian`: `Ctrl+Alt+T`.  
* `Windows`: "`Win+R, powershell, Enter`".  

Enter the following commands:

</p>

```bash
# install fnschool.
pip install -U fnschool

# Making canteen daybook.
python -m fnschoo1.manage migrate # update database.
## start fnschoo1.
python -m fnschoo1.manage
```

<h2 id="credits">
    Credits
</h2>
<p>
    This software uses the following open source packages:
    <ul>
        <li><a href="https://pandas.pydata.org/">pandas</a></li>
        <li><a href="https://numpy.org/">numpy</a></li>
        <li><a href="https://openpyxl.readthedocs.io/">openpyxl</a></li>
        <li><a href="https://github.com/tox-dev/platformdirs">platformdirs</a></li>
        <li><a href="https://matplotlib.org/">matplotlib</a></li>
    </ul>
</p>

<h2 id="support">
    Support
</h2>
<h3>
    Buy me a `coffee`:
</h3>  

![Buy me a "coffee".](https://raw.githubusercontent.com/larryw3i/funingschool/master/Documentation/images/9237879a-f8d5-11ee-8411-23057db0a773.jpeg)

<h2 id="license">
    License
</h2>

<a href="https://github.com/larryw3i/funingschool/blob/master/LICENSE">
    GNU LESSER GENERAL PUBLIC LICENSE Version 3
</a>
