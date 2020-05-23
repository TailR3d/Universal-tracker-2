import json
import os

from exceptions import *
import item_manager
import leaderboard


class Project:
    """Keep track of items for a project"""

    def __init__(self, config_file):
        self.items = item_manager.Items() # Create items object
        self.leaderboard = leaderboard.Leaderboard() # Create leaderboard object
        self.config_path = config_file

        with open(config_file, 'r') as jf: # Open project config file
            configfile = json.loads(jf.read()) # Load project config

            # Put project config into dictionaries
            self.meta = configfile['project-meta']
            self.status = configfile['project-status']
            self.automation = configfile['automation']

        # Get item files
        self.items_folder = os.path.join('projects', self.meta['items-folder'])
        self.item_files = []
        
        for file in os.listdir(self.items_folder):
            if file.endswith('.txt'):
                self.item_files.append(file)

        self.item_files.sort()

        if not self.status['paused']: # If not paused
            try:
                self.queue_next_items() # Load items into queue
            except IndexError:
                print(f"[{self.meta['name']}] Project has no items")

        # Check if there is a leaderboard json file
        self.leaderboard_json_file = os.path.join('projects', f"{self.meta['name']}-leaderboard.json")
        if os.path.isfile(self.leaderboard_json_file):
            # Load leaderboard stats from file
            self.leaderboard.loadfile(self.leaderboard_json_file)

    def saveproject(self):
        """Save project files"""

        if not self.status['paused']: # Make sure project is not paused
            # Write parsed file back to disk. This
            # file will be loaded first upon startup.
            self.items.savefile(os.path.join(self.items_folder, '.queue-save.txt'))

            # Save leaderboard
            self.leaderboard.savefile(self.leaderboard_json_file)

    def update_config_file(self):
        """Write changed config back to the config file"""

        configfile = {}
        configfile['project-meta'] = self.meta
        configfile['project-status'] = self.status
        configfile['automation'] = self.automation

        with open(self.config_path, 'w') as jf:
            jf.write(json.dumps(configfile))

    def queue_next_items(self):
        """Get next items file, and load it into queue"""

        # Get file from list, and remove it from the list.
        items_file = os.path.join(self.items_folder, self.item_files.pop(0))
        self.items.loadfile(items_file) # Queue items

        print(f"[{self.meta['name']}] Added {items_file.split(os.sep)[-1]} to the queue")

        # Remove the text file so it will not load again
        os.remove(items_file)

    # Wrappers for varius tasks
    def get_item(self, username, ip):
        if self.status['paused']: # Check if project is paused
            raise ProjectNotActiveException()

        if len(self.items.queue_items) == 0: # Check if queue is empty
            try:
                self.queue_next_items()
            except IndexError:
                raise NoItemsLeftException()

        item_name = self.items.getitem(username, ip)

        print(f"[{self.meta['name']}] {username} got item {item_name}")

        return item_name

    def heartbeat(self, item_name, ip):
        return self.items.heartbeat(item_name, ip)

    def finish_item(self, item_name, itemsize, ip):
        username = self.items.finishitem(item_name, ip)

        print(f"[{self.meta['name']}] {username} finished item {item_name}")

        # Add item to downloader's leaderboard entry
        self.leaderboard.additem(username, itemsize)

    def get_leaderboard(self):
        return self.leaderboard.get_leaderboard()
