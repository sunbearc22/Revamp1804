#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
'''
Module to query, install and remove a GNOME Display Manager(GDM) theme in
Ubuntu 18.04 from cmdline.

Optional Arguments of this Module:
--install - path of the GDM CSS file that you want to install.
--remove  - path of the GDM CSS file that you want to remove.. 
   
Author      : sunbear.c22@gmail.com
Created on  : 2019-10-12
Modified on : 

                            INTRODUCTION:
The appearance of the Ubuntu 18.04 GDM is managed by the Debian alternatives
system. It's root file is located at /etc/alternatives/gdm3.css and is
symbolically linked to /usr/share/gnome-shell/theme/gdm3.css.

By default, these symbolic links have been instructed to use the Ubuntu
Cascading Style Sheet(CSS) that is located at
/usr/share/gnome-shell/theme/ubuntu.css to style the GDM.

When a different GDM style/theme is preferred, you can install it by doing 
these four procedures:

1. Copy the preferred GDM theme directory into the direcotry called
   /usr/share/gnome-shell/theme. The preferred GDM theme directory shall
   contain the theme's CCS and all other associated files. Please see the
   below section on "REQUIRED GDM THEME DIRECTORY & FILE STRUCTURE" for
   details. After this copy procedure, the location of the preferred theme
   CSS file will be at /usr/share/gnome-shell/theme/mytheme/mytheme.css.
   
2. Use the cmdline "update-alternatives" tool to install and select the 
   preferred theme CSS file to update the Debian alternatives system.
   
3. Replace the "ubuntu.css" value of the "stylesheet" key found in the json
   file /usr/share/gnome-shell/modes/ubuntu.json to the preferred theme
   CSS file path. Note, the state value here is to be relative to
   /usr/share/gnome-shell/theme, i.e. "mytheme/mytheme.css".

4. Press keyboard keys "Alt+F2" followed by "r+Return" to restart the GDM. 
   This script will not perform this step; the user shall have to ensure
   they performed. 

Visible changes to the GDM will take place after procedures 2, 3, and 4 are
performed. If 'user-theme@gnome-shell-extensions.gcampax.github.com' is
enabled, the follow will happen:
 - Procedure 2 will effect style changes to the loginscreen. It's widgets
   and wallpaper will be updated.
 - Procedure 3 will effect style changes to the unlockscreen and lockscreen.
   The wallpaper specified by "mytheme/mytheme.css" selector called
   "#lockDialogGroup{}" will appear in the unlockscreen. The widgets of the
   unlockscreen and the lockscreen will also adhere to the preferred theme. 
 - Procedure 4, the restaring of the GDM, ensures that the GDM theme/style
   changes are implemented. Manually, one can do procedures 2+4, 3+4, and
   2+3+4 To see the style changes. This script performs procedures 1+2+3
   sequentially.

                               WARNING:
ANY ERROR IN /usr/share/gnome-shell/theme/mytheme/mytheme.css CAN MESS UP
YOUR UBUNTU 18.04 SYSTEM AND CAUSEYOU A LOT OF PAIN TO RECOVER YOUR SYSTEM.
                            BE VERY CAREFUL.

            REQUIRED GDM THEME DIRECTORY & FILE STRUCTURE:
MyTheme/                       # theme's main directory
MyTheme/mytheme.css            # theme's CSS file
MyTheme/lockDialogGroup.jpg    # loginscreen and unlockscreen wallpaper
MyTheme/<sub-directories>      # theme's sub-directories that is
                                 accessed by the theme's CSS file

                        HOW THIS MODULE WORK:
Its contains two key parts:
(a) It has a command-line interface that is facilitated by python3 "argparse"
    module.
(b) The heavy lifting of querying, installing and removing a GDM theme is
    done by class "GDM3css".

Cmdline to Query gdm3.css alternatives:
$ python3.6 gdm3css.py
    
Cmdline to Install GDM theme:
$ sudo python3.6 gdm3css.py --install <path to where the GDM CSS file that is to be installed is>

Cmdline to REMOVE GDM theme:
$ sudo python3.6 gdm3css.py --remove <path to where the GDM CSS file that is to be removed is>

'''
from pathlib import Path, PosixPath
from shutil import copy2, copytree, SameFileError, rmtree
from subprocess import run, PIPE
import argparse
import json
import mimetypes
import sys


class CSSFileTypeError(Exception):
    pass


class GDM3css:
    '''Class to query, load, install and remove a Ubuntu 18.04 GNOME Display
       Manager(GDM) Theme.

    Arguments:
      install - path of the GDM CSS file that you want to install.
      remove  - path of the GDM CSS file that you want to remove.
      
    Attributes:
      install - same as above.
      remove  - same as above.
      query   - stdout from cmdline "update-alternatives --query gdm3.css" stored in a list.
      link    - path of gdm3.css.
      best    - alternative path of gdm3.css if selected by auto mode.
      value   - selected alternative path of gdm3.css .
      status  - whether "manual" or "auto" mode is used to select gdm3.css alternative. 
      max     - maximum priority value of all the installed gdm3.css alternatives.

    User Methods:
      installcss - install your GDM Cascading Style Sheet as gdm3.css.
      removecss  - remove/uninstall your GDM Cascading Style Sheet.
    '''
    
    #Class Variable
    GNOME_SHELL_THEME = Path( '/usr/share/gnome-shell/theme' )
    
    #Class Methods
    def __init__( self, install=None, remove=None,  ) :

        def _get( qvalue ):
            return Path( [ line[ line.index('/') : ] for line in self.query if qvalue in line ][0] )

        self.install = install #<class 'pathlib.PosixPath'>
        self.remove = remove   #<class 'pathlib.PosixPath'>
        self.query = run( [ 'update-alternatives', '--query', 'gdm3.css' ],
                          stdout=PIPE, encoding="utf-8" ).stdout.splitlines() #<class 'list'>
        self.link   = _get( 'Link:' )  #<class 'pathlib.PosixPath'>
        self.best   = _get( 'Best:' )  #<class 'pathlib.PosixPath'>
        self.value  = _get( 'Value:' ) #<class 'pathlib.PosixPath'>
        self.status = [ line[ line.index(':')+2 : ] for line in self.query if 'Status:' in line ][0] #<class 'str'>
        self.max = max( [ int( line[ line.index(':')+1 : ] ) for line in self.query if 'Priority:' in line ] ) #<class 'int'>
        print()
        #if install:
        #    print( f'self.install = {self.install} {type(self.install)}' )  #For debugging
        #if remove:
        #    print( f'self.remove = {self.remove} {type(self.remove)}' )  #For debugging
        #if install is None and remove is None:
        #print( f'self.query ={self.query} {type(self.query)}' )   #For debugging
        #print( f'self.link  ={self.link} {type(self.link)}' )     #For debugging
        #print( f'self.best  ={self.best} {type(self.best)}' )     #For debugging
        #print( f'self.value ={self.value} {type(self.value)}' )   #For debugging
        #print( f'self.status={self.status} {type(self.status)}' ) #For debugging
        #print( f'self.max   ={self.max} {type(self.max)}' )       #For debugging


    def _path(self, tgt):
        '''Method to take in only str() and pathlib.Path() objects and ensure
        that only a pathlib.Path() object is returned.'''
        if isinstance( tgt, str ):
            return Path( tgt )
        elif isinstance( tgt, Path ):
            return tgt
        else:
            raise TypeError( f'{tgt} must be a str() or pathlib.Path() object.' )
        

    def _recursive_overwrite(self, src, dst):
        '''Method to recursively copy item(s) from src to dst. If the item
        exist, it will be overwritten.'''
        #print( f'\ndef _recursive_overwrite(self, src, dst):' )
        #print( f'src={src}' )
        #print( f'dst={dst}' )
        src = self._path( src ) #ensure src is a pathlib.Path() object
        dst = self._path( dst ) #ensure dst is a pathlib.Path() object
        if src.is_dir():
            #print( f'if src.is_dir():' )
            if not dst.is_dir():
                dst.mkdir()
            files = [ x for x in src.iterdir() ]
            #print( f'files = {files}' )
            for f in files:
                #print( f'\nf = {f}' )
                #print( f'f.name = {f.name}' )
                #print( f'src.joinpath( f.name ) = {src.joinpath( f.name )}')
                #print( f'dst.joinpath( f.name ) = {dst.joinpath( f.name )}')
                self._recursive_overwrite(
                    str( src.joinpath( f.name ) ), str( dst.joinpath( f.name ) ) )
        else:
            #print( f'else:' )
            try:
                #print( f'copy2( {src}, {dst} )' )
                copy2( src, dst )
            except SameFileError:
                #print( f'except SameFileError:' )
                src.replace( dst )


    def _is_gdm3css_alternative( self, src ):
        '''Method to determine whether src, a pathlib.Path() object, exists and 
        if it is a gdm3.css alternative.'''
        #print( f'src = {src} {type(src)}' )
        if 'css' not in mimetypes.guess_type( str(src) )[0] :
            raise CSSFileTypeError( f'{src} is not a CSS file.' )
        result = True in [ True for line in self.query if str(src) in line ]
        #print( f'result = {result}' )
        return result


    def _update_ubuntujson( self, value ):
        '''Method to update /usr/share/gnome-shell/modes/ubuntu.json with the 
        CSS file path relative to /usr/share/gnome-shell/theme. Argument "value"
        must be a str object.'''
        #print( f'\ndef _update_ubuntujson( self, value ):' )
        with open( '/usr/share/gnome-shell/modes/ubuntu.json', "r+" ) as file:
            data = json.load( file )
            data[ "stylesheetName" ] = value
            file.seek( 0 )  # rewind
            json.dump( data, file, indent=4 )
            file.truncate()


    def load_files( self ):
        '''Load GDM style directories and files into /usr/share/gnome-shell/theme. '''
        #print( f'\ndef load_files( self ):' )
        src = self.install.parent
        dst = GDM3css.GNOME_SHELL_THEME / src.name 
        #print( f'src={src} {type(src)}')
        #print( f'dst={dst} {type(dst)}' )  #For debugging

        #1. Load GDM Cascading Style Sheet and its associate files
        try:
            #print( 'copytree( src, dst )' )
            copytree( src, dst )
        except FileExistsError:
            print( 'FileExistsError:' )
            self._recursive_overwrite( src, dst )

        #2. Place wallpaper of unlockscreen and loginscreen wallpaper in gnome-shell/theme
        #   -- it is read by revamp1804.css
        sierra = Path().home()/'.local'/'share'/'backgrounds'/'Sierra-wallpapers'/'Sierra2.jpg'
        warty = Path( '/usr/share/backgrounds/warty-final-ubuntu.png' )
        dst1 = dst/'assets'/'lockDialogGroup.jpg'
        #print( f'sierra={sierra} {type(sierra)}' )  #For debugging
        #print( f'warty={warty} {type(warty)}' )  #For debugging
        #print( f'dst1={dst1} {type(dst1)}' )  #For debugging
        #print( f'sierra.exists()={sierra.exists()} {type(sierra.exists())}' )  #For debugging
        if sierra.exists():
            copy2( sierra, dst1 ) #Use Sierra theme wallpaper
            print('#Using Sierra theme wallpaper')
        else:
            copy2( warty, dst1 ) #Use Ubuntu18.04 default wallpaper
            print('#Using Ubuntu18.04 default wallpaper')


    def installcss( self ):
        '''Method to install a GDM theme ".css" file as a gdm3.css alternative
           and be used in /usr/share/gnome-shell/modes/ubuntu.json.
        '''
        def _config_alternatives( tgt ):
            if 'auto' not in self.status:
                run( ['update-alternatives', '--auto', 'gdm3.css' ] ) #Ensure auto mode is used
            run( [ 'update-alternatives', '--install', self.link, 'gdm3.css', tgt, str(self.max + 1) ] )
            print( f'{tgt} is now gdm3.css alternative.' )

        css = GDM3css.GNOME_SHELL_THEME / self.install.relative_to( self.install.parents[1] )
        #print( f'css={css} {type(css)}' )  #For debugging

        #1. Copy preferred theme folder to /usr/share/gnome-shell/theme 
        #   if preferred theme CSS file isn't there.
        #if not css.exists():
        #    self.load_files()
        self.load_files()
        
        #2. Install preferred theme CSS file as gdm3.css alternative
        #   - if it is not installed as a gdm3.css alternative, install and select it.
        #   - if it is already selected as the gdm3.css alternative, do nothing.
        #   - if it is installed but is not selected, then select it.
        if not self._is_gdm3css_alternative( css ):
            #print( f'if not self._is_gdm3css_alternative( css ):' )
            _config_alternatives( css )
            pass
        elif self.value.samefile( css ):
            print( f'{css} is already a gdm3.css alternative.' )
        else:
            #print( f'else' )
            run( [ 'update-alternatives', '--remove', 'gdm3.css', str(css) ] )
            self.__init__( install=self.install )
            _config_alternatives( css )

        #3. Reflect it /usr/share/gnome-shell/modes/ubuntu.json
        value = str( css.relative_to( str(GDM3css.GNOME_SHELL_THEME) ) )
        #print( f'value={value} {type(value)}' )  #For debugging
        self._update_ubuntujson( value )


    def removecss( self ):
        '''Method to remove "ubuntu.css" file as a gdm3.css alternative
           and in /usr/share/gnome-shell/modes/ubuntu.json.
        '''
        #print( f'\ndef removecss( self ):' )
        #1. Ensure /usr/share/gnome-shell/theme/ubuntu.css exist.
        installer_dir = Path().absolute()
        #print( f'installer_dir={installer_dir} {type(installer_dir)}' )  #For debugging
        src = installer_dir / Path('resources/original/ubuntu_theme/ubuntu.css')
        #print( f'src={src} {type(src)}' )  #For debugging
        ubuntu = Path( '/usr/share/gnome-shell/theme/ubuntu.css' )
        #print( f'ubuntu={ubuntu} {type(ubuntu)}' )  #For debugging
        if not ubuntu.exists():
            copy2( str( src ), str(ubuntu) )
            print( f'Copied ubuntu.css to location.')
        else:
            print( f'{ubuntu} exists.' )
        #2. Update /usr/share/gnome-shell/modes/ubuntu.json to use ubuntu.css.
        self._update_ubuntujson( 'ubuntu.css' )
        #3. Remove the CSS file of the theme that is to be removed from the
        #   Debian alternatives system and revert to using
        #   /usr/share/gnome-shell/theme/ubuntu.css 
        run( [ 'update-alternatives', '--remove', 'gdm3.css', str(self.remove) ] )
        run( [ 'update-alternatives', '--auto', 'gdm3.css' ] ) #Ensure auto mode is used
        self.__init__( remove=self.remove )
        #   If auto mode does not select usr/share/gnome-shell/theme/ubuntu.css,
        #   then set it manually.
        if not self.value.samefile( ubuntu ):  
            run( [ 'update-alternatives', '--set', 'gdm3.css', str(ubuntu) ] )
        #4. Remove the selected theme directory from directory
        #   /usr/share/gnome-shell/theme. E.g. if selected them is at
        #   /usr/share/gnome-shell/theme/mytheme/mytheme.css, we want to
        #   remove /usr/share/gnome-shell/theme/mytheme, which is the parent of
        #   mytheme.css.
        tgt = self.remove.parent
        #print( f'tgt={tgt} {type(tgt)}' )  #For debugging
        try:
           rmtree( tgt )
        except:
           print('Error while deleting directory')
        else:
            print( f'Completed: {tgt} is removed.')


def _installpath( src ):
    #print('def _installpath( src ):')
    src = _absolutepath( src )
    _cssexist( src )
    return src


def _removepath( src ):
    #print('def _removepath( src ):')
    src = _absolutepath( src )
    _cssexist( src )
    gstheme = GDM3css.GNOME_SHELL_THEME
    try:
        src.relative_to( gstheme )
    except ValueError:
        sys.exit( f'ValueError: {src} is not a child of {gstheme}.' )
    else:
        return src


def _absolutepath( src ):
    '''Function to get the absolute path of src.'''
    #print('def _absolutepath( src ):')
    src = Path(src)
    #print(f'src = {src}')
    if not src.is_absolute():
        #print(f'if not src.is_absolute():')
        file = Path.cwd()
        for part in src.parts:
            file = file.joinpath( part )
        src = file
    #print(f'src = {src}')        
    return src


def _cssexist( src ):
    '''Function to determine if "src", a pathlib.Path() object, exist and if \
    it can be a gdm3.css alternative.'''
    if not src.exists():
        sys.exit( f'FileExistsError: {src} does not exist.' )
    if 'css' not in mimetypes.guess_type( str(src) )[0] :
        sys.exit( f'CSSFileTypeError: {src} is not a CSS file.' )
    

def main():
    #1. Setup the argument parser 
    parser = argparse.ArgumentParser()

    #2. Define arguement
    parser.add_argument( '--install', type=_installpath, help='path of the GDM CSS file that you want to install.' )
    parser.add_argument( '--remove', type=_removepath, help='path of the GDM CSS file that you want to remove.' )
    
    #3. Get the arguements
    args = parser.parse_args()
    #print( f'args.install = {args.install}' )#for debugging
    #print( f'args.remove  = {args.remove}' ) #for debugging

    #4. Set up the permissible operations from cmdline.
    if args.install is None and args.remove is None :
        print('QUERY')
        gdm3 = GDM3css()
    elif args.install and args.remove is None :
        #print('INSTALL')
        #print( f'type(args.install) = {type(args.install)}' )
        gdm3 = GDM3css( install=args.install )
        gdm3.installcss()
    elif args.install is None and args.remove :
        #print('REMOVE')
        gdm3 = GDM3css( remove=args.remove )
        gdm3.removecss()
    else:
        parser.print_help()
        print( 'Please use command syntax.' )
    
    

if __name__ == '__main__':
    main()
    
  
    ## This script needs to be executed by sudo. ## 
