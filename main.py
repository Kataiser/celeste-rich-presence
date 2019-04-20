import os
import sys
import time
from operator import itemgetter

sys.path.append(os.path.abspath(os.path.join('python', 'packages')))
sys.path.append(os.path.abspath(os.path.join('python')))
import psutil
import psutil._exceptions as ps_exceptions
from bs4 import BeautifulSoup
from discoIPC import ipc


def main():
    chapter_names = ['Prologue', 'Chapter 1: Forsaken City', 'Chapter 2: Old Site', 'Chapter 3: Celestial Resort', 'Chapter 4: Golden Ridge', 'Chapter 5: Mirror Temple',
                     'Chapter 6: Reflection', 'Chapter 7: The Summit', 'Epilogue', 'Chapter 8: Core']
    chapter_pics = ['intro', 'city', 'oldsite', 'resort', 'golden', 'temple', 'reflection', 'summit', 'intro', 'core']
    sides = {'Normal': ('A-Side', 'aside'), 'BSide': ('B-Side', 'bside'), 'CSide': ('C-Side', 'cside')}

    start_time = int(time.time())
    activity = {'details': 'In menus',  # this is what gets modified and sent to Discord via discoIPC
                'timestamps': {'start': start_time},
                'assets': {'small_image': ' ', 'small_text': 'In menus', 'large_image': 'logo', 'large_text': 'Celeste'},
                'state': 'yeet'}
    client_connected = False

    while True:
        game_is_running = False
        discord_is_running = False

        for process in psutil.process_iter():
            if game_is_running and discord_is_running:
                break
            else:
                try:
                    with process.oneshot():
                        p_name = process.name()

                        if p_name == "Celeste.exe":
                            game_location = process.cmdline()[0].replace('Celeste.exe', '')
                            start_time = int(process.create_time())
                            game_is_running = True
                        elif 'Discord' in p_name:
                            discord_is_running = True
                except ps_exceptions.NoSuchProcess:
                    pass
                except ps_exceptions.AccessDenied:
                    pass

                time.sleep(0.001)

        if game_is_running and discord_is_running:
            if not client_connected:
                # connects to Discord
                client = ipc.DiscordIPC('528044034619604992')
                client.connect()
                client_connected = True

            save_files = []
            for save_file in os.listdir(f'{game_location}\\Saves'):
                full_path = f'{game_location}\\Saves\\{save_file}'
                if 'settings' not in save_file:
                    save_files.append((full_path, os.stat(full_path).st_mtime))
            current_save_file_path = sorted(save_files, key=itemgetter(1), reverse=True)[0][0]

            with open(current_save_file_path, 'r', errors='replace') as current_save_file:
                xml_soup = BeautifulSoup(current_save_file.read(), 'xml')

                try:
                    current_save_number = int(current_save_file.name.split('\\')[-1][0]) + 1
                except ValueError:
                    current_save_number = None

            save_slot_name = xml_soup.find('Name').string
            current_area_id = int(xml_soup.find('LastArea').get('ID'))
            current_area_mode = xml_soup.find('LastArea').get('Mode')
            total_deaths = xml_soup.find('TotalDeaths').string
            total_berries = int(xml_soup.find('TotalStrawberries').string)

            current_session = xml_soup.find('CurrentSession')
            if current_session:
                in_area = current_session.get('InArea') == 'true'
            else:
                in_area = True

            for area in xml_soup.find_all('AreaStats'):
                if area.get('ID') == str(current_area_id):
                    current_area_info = area.find_all('AreaModeStats')[list(sides.keys()).index(current_area_mode)]
                    current_area_deaths = current_area_info.get('Deaths')

            if save_slot_name == 'Madeline':
                save_slot_text = ""
            else:
                save_slot_text = f": \"{save_slot_name}\""

            activity['details'] = chapter_names[current_area_id]
            activity['assets']['small_image'] = ' '
            activity['assets']['large_image'] = chapter_pics[current_area_id]
            activity['assets']['small_text'] = f"{chapter_names[current_area_id]} ({sides[current_area_mode][0]})"
            activity['timestamps']['start'] = start_time

            if not current_save_number and current_save_file_path.endswith('\\debug.celeste'):
                activity['state'] = "In debug mode"
                activity['assets']['large_text'] = chapter_names[current_area_id]
            else:
                activity['assets']['large_text'] = f"Totals: {total_deaths} deaths, {total_berries} strawberries (save slot #{current_save_number}{save_slot_text})"

                if time.time() - start_time < 15:
                    activity['state'] = "Loading game"
                elif in_area:
                    activity['state'] = f"{sides[current_area_mode][0]} ({current_area_deaths} deaths)"
                else:
                    activity['state'] = "In level select"

            print(activity['details'])
            print(activity['state'])
            print(activity['assets']['large_text'])
            time_elapsed = time.time() - start_time
            print("{:02}:{:02} elapsed".format(int(time_elapsed / 60), round(time_elapsed % 60)))
            print()

            if not os.path.exists('history.txt'):
                open('history.txt', 'w').close()

            activity_str = f'{activity}\n'
            with open('history.txt', 'r') as history_file_r:
                history = history_file_r.readlines()
            if activity_str not in history:
                with open('history.txt', 'a') as history_file_a:
                    history_file_a.write(activity_str)

            # send everything to discord
            client.update_activity(activity)
        elif not discord_is_running:
            print("{}\nDiscord isn't running\n")
        else:
            if client_connected:
                try:
                    client.disconnect()  # doesn't work...
                except:
                    pass

                raise SystemExit  # ...but this does
            else:
                print("\nCeleste isn't running\n")

            # to prevent connecting when already connected
            client_connected = False

        # rich presence only updates every 15 seconds, but it listens constantly so sending every 5 seconds is fine
        time.sleep(10)


if __name__ == '__main__':
    main()
