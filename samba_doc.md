#### 1.A.i: Create a shared, mounted folder to coordinate across Linux instances:
If you have multiple instances where you want to run experiments, all machines need to be able to read the necessary Python scripts and maintain a database of tuning results. There are multiple ways to do this, but one popular solution is to use Samba. A basic tutorial is included below, but more information is available at [Samba Wiki](https://wiki.samba.org/index.php/Main_Page). If you plan to only use one machine, this step is not neccessary. 

The first step is to choose one linux instance to act as the server which will host the shared files. The others will act as clients. 

Step 1: Create a directory on each client machine where you will mount the samba share. For the sake of consistency we mounted our share at "/srv/samba/hp_tune_grid" on each machine:   

```bash
ssh user@ipaddress 
mkdir /path/to/samba/share/mounted_dir
```

Step 2: 

