import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter.messagebox import showerror
import pandas as pd
import xmltodict
import datetime

# TODO

class App:

    def __init__(self):
        # creating app window
        self.root = tk.Tk()
        self.root.geometry("500x500")
        self.root.title("DJ Set Length")

        # setting input variables
        self.playlist = tk.StringVar()
        self.n_tracks = tk.IntVar()
        self.bpm = tk.IntVar()
        self.vcmd = self.root.register(self.validate_int_input)

        # app header
        self.label = tk.Label(self.root, text="DJ set length checker", font=('calibre', 20, 'bold'))
        self.label.pack(pady=20)

        ### INPUTS ###
        # playlist name
        self.playlist_label = tk.Label(self.root, text="Playlist name:", font=('calibre', 15))
        self.playlist_label.pack()

        self.playlist_entry = tk.Entry(self.root, textvariable=self.playlist)
        self.playlist_entry.pack()
        self.playlist_entry.focus()

        # bpm
        self.bpm_label = tk.Label(self.root, text="Playlist bpm:", font=('calibre', 15))
        self.bpm_label.pack()

        self.bpm_entry = tk.Entry(self.root, textvariable=self.bpm, validate="key", validatecommand=(self.vcmd, "%P"))
        self.bpm_entry.pack()

        # number of tracks
        self.n_tracks_label = tk.Label(self.root, text="Number of tracks:", font=('calibre', 15))
        self.n_tracks_label.pack()

        self.n_tracks_entry = tk.Entry(self.root, textvariable=self.n_tracks, validate="key", validatecommand=(self.vcmd, "%P"))
        self.n_tracks_entry.pack()

        # button
        self.button = tk.Button(self.root, text="Calculate", font=('calibre', 15), command=self.calculate_length)
        self.button.pack(pady=5)

        # window loop
        self.root.mainloop()


    
    ######### METHODS #########

    def calculate_length(self) -> None:
        # get playlist dataframe
        df = self.get_playlist_df()
        if not isinstance(df, pd.DataFrame):
            return

        # iterate through df to calculate each track length - from cuepoint A to G (cue A=0, cue G=6)
        total_length = 0
        tracks_output_str = ""
        for row in df.iterrows():
            track_name = row[1]['@Name']
            track_num = row[1]['@Number']
            if isinstance(row[1]['TEMPO'], dict):
                track_bpm = row[1]['TEMPO']['@Bpm']
            elif isinstance(row[1]['TEMPO'], list):
                track_bpm = row[1]['TEMPO'][0]['@Bpm']
            track_bpm = float(track_bpm)
            bpm_change = self.bpm.get()/track_bpm

            cues = row[1]['POSITION_MARK']

            start = None
            end = None
            for cue in cues:
                if cue['@Num'] == '0':
                    start = float(cue['@Start'])
                    start = start/bpm_change
                elif cue['@Num'] == '6':
                    end = float(cue['@Start'])
                    end = end/bpm_change
                else:
                    continue
                
            if end:
                track_length = end - start
                total_length += track_length
                tracks_output_str += f'{track_num}. "{track_name}" length: {str(datetime.timedelta(seconds=track_length)).split(".")[0]} \n'
            else:
                tracks_output_str += f'Track "{track_name}" has no end cue, skipping \n'

        tracks_output_str = tracks_output_str.rstrip()
        playlist_output_str = f'{self.playlist.get()} has {str(datetime.timedelta(seconds=total_length)).split(".")[0]}'

        self.destroy_output()

        # tracks lenght output
        self.tracks_output = ScrolledText(self.root, height=10, width=50, state='normal', font=('calibre', 12))
        self.tracks_output.pack(pady=5)

        self.tracks_output.insert(tk.INSERT, tracks_output_str)
        self.tracks_output.config(state='disabled')

        # full playlist length output
        self.playlist_len_output = tk.Label(self.root, text=playlist_output_str, font=('calibre', 15, 'bold'))
        self.playlist_len_output.pack(pady=10)



    def get_playlist_df(self) -> pd.DataFrame:
        playlist_name = self.playlist.get()
        n_tracks = self.n_tracks.get()

        # import playlist data
        try:
            df_playlist = pd.read_fwf(f'/Users/tomek/Documents/rekordbox/{playlist_name.upper()}.txt', encoding='latin')
        except FileNotFoundError:
            showerror(title='No such file', message=f'No file for "{playlist_name}" playlist. Check if the name is correct or try downloading a playlist .txt from rekordbox')
            return None

        # clean playlist data
        df_playlist = df_playlist[df_playlist.columns[0]].apply(lambda x: '; '.join(x.split('\t', 3)[:3]))
        df_playlist = df_playlist.str.split(';',expand=True)
        df_playlist = df_playlist[[0, 2]]
        df_playlist[2] = df_playlist[2].str.strip()
        df_playlist.columns = ['@Number','@Name']
        df_playlist.dropna(inplace=True)
        df_playlist['@Number'] = df_playlist['@Number'].str.replace('\x00', '', regex=False).astype(int)
        df_playlist.sort_values(by='@Number', inplace=True)

        # select n tracks
        df_current_tracks = df_playlist.head(n_tracks)
        df_current_tracks.loc[:,'@Name'] = df_current_tracks['@Name'].str.replace('\x00', '', regex=False)

        # import collection data
        with open('/Users/tomek/Documents/rekordbox/rekordbox.xml') as fd:
            doc = xmltodict.parse(fd.read())
        doc = doc['DJ_PLAYLISTS']['COLLECTION']['TRACK']
        df_library = pd.DataFrame(doc)

        df_library = df_library[df_library['@Location'].str.contains('file://localhost/Users/tomek/Desktop/DJ%20VAULT/')]

        # calculate track times
        df = df_current_tracks.merge(df_library, on='@Name')

        return df



    def destroy_output(self) -> None:
        if 'tracks_output' in self.__dict__.keys():
            self.tracks_output.pack_forget()
        else:
            pass

        if 'playlist_len_output' in self.__dict__.keys():
            self.playlist_len_output.pack_forget()
        else:
            pass



    def validate_int_input(self, P):
        if P.isdigit() or P == "":
            return True
        else:
            return False


App()