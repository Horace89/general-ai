:: Batch file to run torcs with some settings
:: First parameter (%1) is xml config file
:: Second parameter (%2) is path to java classes with torcs client
cd "C:/Program Files (x86)/torcs"
start /b wtorcs.exe -r %1 -t 1000000 -nofuel -nodamage -nolaptime
::start /b wtorcs.exe -r ./config/raceman/race_config.xml -t 1000000 -nofuel -nodamage -nolaptime
::timeout 2 /nobreak
PING 1.1.1.1 -n 1 -w 1000 > NUL
java -cp %2 scr.Client scr.GeneralAIDriver port:3002 directory:%3