@ECHO OFF
SET LOGCHARTS=C:\LOGGER20\CHARTS
SET LOGMACROS=C:\LOGGER20\MACROS
cd C:\logger20\projects
md %1
cd %1
logger20
echo on
REM Copy Data to Floppy Disk !
