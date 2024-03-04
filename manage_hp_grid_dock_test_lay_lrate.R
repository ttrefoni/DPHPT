
library(tidyverse)

epochs <- seq(30,50,5)
batch_size <- c(64,128,256)
units1 <- c(100,150,200,250)
units2 <- c(50,100,150)
lrate <- c(.001,.01,)

hps <- expand_grid(epochs=epochs,batch_size=batch_size,units1=units1,units2=units2,lrate=lrate)

#write to file
write_csv(hps,"/srv/samba/hp_tune_grid/hps_original_grid.csv")

hps <- read_csv("/srv/samba/hp_tune_grid/hps_original_grid.csv")

#how many hps to test in this instance 
to_test <- 20

# Specify the path to the tested file
hp_tested_fp <- "/srv/samba/hp_tune_grid/hps_tested.csv"
#read in previously tested hps
# Check if the file exists
if (file.exists(hp_tested_fp)) {
  #if exists read csv 
  hps_tested <- read_csv(hp_tested_fp)
  #and exclude previously tested hps from available combos
  hps_avalible <- anti_join(hps, hps_tested, by = c("epochs", "batch_size", "units1", "units2","lrate"))
} else {
  #If no tested hps are found, set to existing grid 
   hps_avalible <- hps
}


#take a random sample of hps 
hps_to_test <- sample(c(1:nrow(hps_avalible)),size=20)
hps_test <- hps_avalible[hps_to_test,]

#pull out hostname and write file of currenntly selected hps 
hostname <- system("hostname", intern = TRUE)
write_csv(hps_test,str_c("/srv/samba/hp_tune_grid/hps_selected_",hostname,".csv"))

#save tested hp as own csv
# Check if hps tested file exists 
if (file.exists(hp_tested_fp)) {
  #if exists read csv 
  hps_tested <- read_csv(hp_tested_fp)
  #and bind new test to the csv 
  hps_tested <- rbind(hps_tested,hps_test)
  write_csv(hps_tested,hp_tested_fp)
} else {
  #initiate new hps tested file 
  hps_tested <- hps_test
  write_csv(hps_tested,hp_tested_fp)
}

#update hps available by excluding hps tested 
hps_avalible <- anti_join(hps, hps_tested, by = c("epochs", "batch_size", "units1", "units2","lrate"))

#write hps still available 
write_csv(hps_avalible,"/srv/samba/hp_tune_grid/hps_avalible.csv")
