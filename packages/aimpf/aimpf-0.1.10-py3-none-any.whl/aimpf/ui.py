import os
import tkinter as tk
from pycarta.auth import CartaProfileUI
from tkinter import Frame, Label


class AimpfCartaProfile(CartaProfileUI):
    """
    A custom CartaProfile for the AIMPF project.
    """

    class LabelWithGet(Label):
        def __init__(self, *args, **kwds):
            super().__init__(*args, **kwds)

        def get(self):
            return self.cget("text").strip()

    def __init__(self, *args, profile: None | str=None, **kwds):
        self.profile = profile or os.environ.get('CARTA_PROFILE', 'aimpf')
        super().__init__("Carta login credentials for AIMPF", *args, **kwds)
    
    def insert_profile_name_field(self, frame: None | Frame = None):
        frame = frame or self._frames[-1]
        # The name "_profileComboBox" is a misnomer, but is kept
        # to maintain the construction order in CartaProfileUI
        self._profileComboBox = AimpfCartaProfile.LabelWithGet(text=self.profile)
        self._profileComboBox.pack(fill=tk.X)


if __name__ == '__main__':
    app = AimpfCartaProfile()
