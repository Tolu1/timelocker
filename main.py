from locker import Timelock

# dir = 'C:\Intel\Logs\Locked'
dir = './test'
tl = Timelock(date='14-08-2021', dir=dir, email='tolugbesan@gmail.com')
# tl.lock()

future_message = 'gAAAAABhDpI-OPQTDdbMyzGrpNcDih8TSDrcU1fi8nOdxLcwyu19mbGAehn5Mg_Hbmva3KdYGISvcEUOCQKvUUvch8DyfVQaSzC5hKlZEaRw7Pc-DTISuPZ378nz_9pSFOs_YJO7_QZA'
tl.unlock(email_message=future_message)

# with open('./encryption-774809094.key', 'rb') as file:
#     encryption_key = file.read()
#     tl.unlock(encryption_key=encryption_key)