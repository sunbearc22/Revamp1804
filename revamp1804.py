#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
'''
Program to give Ubuntu 18.04 a Sierra-light-ish desktop look and feel..

To implement:
  $ python3.6 revamp1804.py --install
To undo ( i.e. revert back to a fresh Ubuntu 18.04 look and feel ):
  $ python3.6 revamp1804.py --remove
Note: This program will access Administration privilege during execution.

Tasks:
  (a) Install certain \'deb\' packages (and ppa) into Ubuntu 18.04. 
  (b) Install and enable themes and extensions:
      Themes :-
        Apps  - McHigh Sierra
        Icons - Cupertino iCons Collection
        Cursor- MacOS MOD
        Fonts - SanFranciscoFont, macfonts
        GDM   - Revamp1804 (adapted from High Ubunterra*
                * https://www.gnome-look.org/p/1207015/ High Ubunterra.
      Extensions:-
        Always Zoom Workspaces, Arc Menu, Blyr, Dash to Dock,
        Dynamic Panel Transparency, EasyScreenCast, Log Out Button, NetSpeed,
        Removable Drive Menu, Screenshot Tool, Suspend Button, User Themes,
        Workspace Indicator
  (c) Customize the settings of these applications, extensions and more.
  (d) Install a nautilus script to allow an easy change of the desktop and
      screensaver wallpapers.
'''
import argparse
import getpass
import os
import platform
import sys
import time
import concurrent.futures as cf
from io import BytesIO
from itertools import repeat
from json import loads as jsonloads
from pathlib import Path
from shutil import copy2, copytree, rmtree
from subprocess import run, PIPE, STDOUT, CalledProcessError
from threading import current_thread
from urllib.request import Request, urlopen
from urllib.error import URLError
from zipfile import ZipFile

#=================
# Global Variables
#=================
__author__ = "sunbearc22"
__copyright__ = "Copyright 2019, sunbear.c22@gmail.com"
__credits__ = ["sunbearc22"]
__license__ = "GPL-3.0-only"
__version__ = "0.1-dev"
__maintainer__ = "sunbearc22"
__email__ = "sunbear.c22@gmail.com"
__status__ = "Development"

# Directories
HOME = Path.home() #user home directory
INSTALLER_DIR = Path().absolute()
print( f'INSTALLER_DIR = {INSTALLER_DIR}')
if os.getuid() == 0:
    sys.exit( print( f'\nQuit: Don\'t run this script with \'sudo\' privilege.\n'
                     '      Re-run this script as normal user.' ) )
else:
    GLIB2_SCHEMAS = HOME/'.local'/'share'/'glib-2.0'/'schemas'
    GSEXTENSIONS = HOME/'.local'/'share'/'gnome-shell'/'extensions'
    ICONS = HOME/'.local'/'share'/'icons'
    FONTS = HOME/'.local'/'share'/'fonts'
    THEMES = HOME/'.local'/'share'/'themes'
    BACKGROUNDS = HOME/'.local'/'share'/'backgrounds'
    GBACKGROUNDS_PROPERTIES =  HOME/'.local'/'share'/'gnome-background-properties'
for _folder in [ GLIB2_SCHEMAS, GSEXTENSIONS, ICONS, FONTS, THEMES, BACKGROUNDS,
                 GBACKGROUNDS_PROPERTIES ]:
    if not _folder.exists() and not _folder.is_dir():
        _folder.mkdir( mode=0o777, parents=True, exist_ok=False )

# Variables
USERNAME = getpass.getuser() # Get OS username
PPA = ['ppa:dyatlov-igor/sierra-theme']
GNOME_DEB_PKGS = [ 
    'dconf-editor', 'gnome-tweak-tool', #Utilities to configure GNOME and GNOME shell 
    'chromium-browser','chrome-gnome-shell', #Allow Chromium browser to install & configure GNOME shell extensions
    'gnome-shell-extension-dashtodock', #GNOME shell dash-to-dock extension
    'arc-theme', #'sierra-gtk-theme-git' is derived from arc-theme (provides an alternative theme to 'sierra-gtk-theme-git'.)
    'gtk2-engines-murrine', 'gtk2-engines-pixbuf', 'sierra-gtk-theme-git', #For Sierra Gtk Theme https://github.com/vinceliuice/Sierra-gtk-theme
    'gir1.2-gtkclutter-1.0', #For GNOME shell extension - Blyr https://github.com/yozoon/gnome-shell-extension-blyr
    'gnome-shell-extensions', 'gnome-menus', 'gir1.2-gmenu-3.0', #For Arc Menu https://gitlab.com/LinxGem33/Arc-Menu/wikis/Arc-Menu-Dependencies        
    'xdotool', #Needed to programmatically simulate keyboard input Alt+F2 followed by r + Return to restart GNOME shell.
    'idle-python3.6',  #Allow user to edit and test this python script
    'libqt5svg5', 'qml-module-qtquick-controls', #For MacOS MOD cursor 
    'libreoffice-style-sifr',# "sifr" symbol style (an adaption of the Gnome symbolic theme), to manually enable in LibreOffice --> Tools --> Option --> LibreOffice --> View --Icon Style.
    ]
REMOVE_DEB_PKGS = [ 
    'gnome-shell-extension-dashtodock', #GNOME shell dash-to-dock extension
    'arc-theme', #'sierra-gtk-theme-git' is derived from arc-theme (provides an alternative theme to 'sierra-gtk-theme-git'.)
    'sierra-gtk-theme-git', #For Sierra Gtk Theme https://github.com/vinceliuice/Sierra-gtk-theme
    #'xdotool', #Needed to programmatically simulate keyboard input Alt+F2 followed by r + Return to restart GNOME shell.
    'libreoffice-style-sifr',# "sifr" symbol style (an adaption of the Gnome symbolic theme), to manually enable in LibreOffice --> Tools --> Option --> LibreOffice --> View --Icon Style.
    ]


#=================
# Functions
#=================
def _extensions_url():
    alwayszoomworkspaces =       'https://extensions.gnome.org/extension-data/alwayszoomworkspaces%40jamie.thenicols.net.v11.shell-extension.zip'
    arc_menu =                   'https://extensions.gnome.org/extension-data/arc-menu%40linxgem33.com.v22.shell-extension.zip'
    blyr =                       'https://extensions.gnome.org/extension-data/blyr%40yozoon.dev.gmail.com.v5.shell-extension.zip'
    dynamic_panel_transparency = 'https://extensions.gnome.org/extension-data/dynamic-panel-transparencyrockon999.github.io.v31.shell-extension.zip'
    EasyScreenCast =             'https://extensions.gnome.org/extension-data/EasyScreenCast%40iacopodeenosee.gmail.com.v38.shell-extension.zip'
    LogOutButton =               'https://extensions.gnome.org/extension-data/LogOutButton%40kyle.aims.ac.za.v3.shell-extension.zip'
    netspeed =                   'https://extensions.gnome.org/extension-data/netspeed%40hedayaty.gmail.com.v29.shell-extension.zip'
    screenshot =                 'https://extensions.gnome.org/extension-data/gnome-shell-screenshot%40ttll.de.v31.shell-extension.zip'
    suspend_button =             'https://extensions.gnome.org/extension-data/suspend-buttonlaserb.v20.shell-extension.zip'
    #user_theme =                 'https://extensions.gnome.org/extension-data/user-theme%40gnome-shell-extensions.gcampax.github.com.v34.shell-extension.zip'
    #workspace_indicator =        'https://extensions.gnome.org/extension-data/workspace-indicator%40gnome-shell-extensions.gcampax.github.com.v36.shell-extension.zip'
    return [ alwayszoomworkspaces, arc_menu, blyr, dynamic_panel_transparency, 
             EasyScreenCast, LogOutButton, netspeed, screenshot, suspend_button, ]


def _icons_url():
    Cupertino =          'https://codeload.github.com/USBA/Cupertino-iCons/zip/master'
    Cupertino_Catalina = 'https://codeload.github.com/USBA/Cupertino-Catalina-iCons/zip/master'
    return [ Cupertino, Cupertino_Catalina ]


def _cursors_url():
    MacOSMOD = 'https://codeload.github.com/douglascomim/MacOSMOD/zip/master'
    return [ MacOSMOD ]


def _fonts_url1():
    San_Francisco_Font_master = 'https://codeload.github.com/AppleDesignResources/SanFranciscoFont/zip/master'
    return [ San_Francisco_Font_master]

    
def _fonts_url2():
    macfonts = 'http://drive.noobslab.com/data/Mac/macfonts.zip'
    return [ macfonts ]


def show_header():
    print()
    print( f'             @@@@@@  @@@@@@@ @       @    @       @       @ @@@@@@')
    print( f'             @     @ @        @     @    @ @      @@     @@ @     @')
    print( f'             @     @ @        @     @   @   @     @ @   @ @ @     @')
    print( f'             @@@@@@  @@@@@@    @   @   @     @    @  @ @  @ @@@@@@')
    print( f'             @   @   @         @   @  @ @@@@@ @   @   @   @ @')
    print( f'             @    @  @          @ @  @         @  @       @ @')
    print( f'             @     @ @@@@@@@     @  @           @ @       @ @\n')
    print( f'          Giving Ubuntu 18.04 a Sierra-light-ish desktop look and feel.\n' )
    print( f'================================================================================\n')


def show_intro():
    show_header()
    check_system_platform_and_Ubuntu_distribution()
    print( f'\nUser : {USERNAME}' )
    print( f'Linux Distro : { " ".join(DISTRO.values()) }\n' )
    time.sleep(1)


def check_system_platform_and_Ubuntu_distribution():
    global DISTRO
    if not 'Linux' in platform.system():
        sys.exit( print( '\nQuit: Non Linux System Platform is detected.' ) )
    linux_distr = platform.linux_distribution()
    if not 'Ubuntu' in linux_distr:
        sys.exit( print( '\nQuit: Non Ubuntu distribution is detected.' ) )
    if '18.04' in linux_distr:
        label = ( 'name', 'version', 'nickname' )
        DISTRO = dict( zip( label, linux_distr ) )
    else:
        sys.exit( print( f'\nQuit: Ubuntu { DISTRO[version] } is not supported.' ) )


def update_apt_repository():
    '''Function to add the required ppas to apt-repository if they do not exist.'''
    #1. Install package to avoid "add-apt-repository: command not found error"
    apt_install( ['software-properties-common'] )
    #2. Add 'ppa:dyatlov-igor/sierra-theme' to apt_repository if it does not
    #   exist.
    repos = [ Path( '/etc/apt/sources.list' ) ]
    repos.extend( [ x for x in Path( '/etc/apt/sources.list.d/' ).iterdir() ] )
    ppas_to_add = PPA
    for repo in repos:
        with open( repo, 'r') as f:
            for line in f:
                if 'deb http' in line:
                    for ppa in PPA:
                        if ppa[4:] in line:
                            ppas_to_add.remove( ppa )
    #print( 'repos =', repos )
    #print( 'ppas_to_add =', ppas_to_add )
    if ppas_to_add:
        for ppa in ppas_to_add:
            add_apt_repository( ppa )
        print( f'\nPPA is updated into apt-repository.' )
    else:
        print( f'\napt-repository is already up to date.' )
    

def runN( cmd ):
    #print( f"\nRunning command: {' '.join(cmd)}" )
    print( f"\n{' '.join(cmd)}" )
    result = run( cmd, stdout=sys.stdout, stderr=sys.stderr, encoding='utf8' )
    return result


def add_apt_repository( ppa ):
    '''Function to add apt sources.list entries. Argument ppa is a string.'''
    cmd = [ 'sudo', 'add-apt-repository', '-y' ]
    cmd.append( ppa )
    runN( cmd )


def apt_update():
    cmd = [ 'sudo', 'apt-get', '-y', 'update' ]
    runN( cmd )


def apt_dist_upgrade():
    cmd = [ 'sudo', 'apt-get', '-y', 'dist-upgrade' ]
    runN( cmd )


def apt_install( pkgs ):
    '''Function to install Debian Package(s). Argument pkgs is a list of string(s).'''
    cmd = ['sudo', 'apt-get', '-y', 'install', ] + pkgs
    runN( cmd )


def install_apt_pkgs():
    apt_install( GNOME_DEB_PKGS )


def apt_remove( pkgs ):
    '''Function to remove Debian Package(s). Argument pkgs is a list of string(s).'''
    cmd = ['sudo', 'apt-get', '-y', 'remove', ] + pkgs
    runN( cmd )


def remove_apt_pkgs():
    apt_remove( REMOVE_DEB_PKGS )


def install_themes_fonts_gsextensions():
    global INSTALLED_GSEXTENSIONS
    macfonts = FONTS / 'macfonts'
    print( f'\nInstalling GNOME Theme Icons, Fonts and Extensions ...' )
    #1. Download extensions, fonts and icons
    start = time.time()
    with cf.ThreadPoolExecutor() as executor:
        extensions = executor.map( install_theme_font_or_gsextension, _extensions_url(), repeat( GSEXTENSIONS ) )
        icons  = executor.map( install_theme_font_or_gsextension, _icons_url(),   repeat( ICONS ) )
        cursor = executor.map( install_theme_font_or_gsextension, _cursors_url(), repeat( ICONS ) )
        font1  = executor.map( install_theme_font_or_gsextension, _fonts_url1(),  [ FONTS ] )
        font2  = executor.map( install_theme_font_or_gsextension, _fonts_url2(),  [ macfonts ]  )
    end = time.time()

    #2. Manually enable GNOME Shell extensions that were installed via "sudo apt-get install gnome-shell-extensions".
    sudo_gsextensions = [ 'user-theme@gnome-shell-extensions.gcampax.github.com',
                          'workspace-indicator@gnome-shell-extensions.gcampax.github.com',
                          'drive-menu@gnome-shell-extensions.gcampax.github.com',
                          'dash-to-dock@micxgx.gmail.com' ]
    for ext in sudo_gsextensions:
        if Path( f'/usr/share/gnome-shell/extensions/{ext}' ).exists():
            run( f'gnome-shell-extension-tool -e {ext}', shell=True)

    #3. Print out results:
    print( f'\nInstalling GNOME Theme Icons, Fonts and Extensions ... Completed in {end-start:.2f} sec' )
    print( f' - {ICONS} = {list(icons) + list(cursor)}' )
    print( f' - {FONTS} = {list(font1) + list(font2)}' )
    INSTALLED_GSEXTENSIONS = list( extensions )
    count = 0
    for i in INSTALLED_GSEXTENSIONS:
        if count == 0:
            print(f" - {GSEXTENSIONS} = ['{i}',")
        else:
            print(f"{'':55}'{i}',")
        count += 1
    print(f"{'':55}]")
    #print( f' - {GSEXTENSIONS} = {INSTALLED_GSEXTENSIONS}' )

    #4. Compile schemas in GLIB2_SCHEMAS
    run( ['glib-compile-schemas', GLIB2_SCHEMAS], stdout=sys.stdout )

    #5. Check compiled schemas in GLIB2_SCHEMAS
    glib_ext_schema = run(
        [f'ls ~/.local/share/glib-2.0/schemas/ | grep org.gnome.shell.extensions' ],
        stdout=PIPE, shell=True ).stdout.decode().splitlines()
    #print( f'glib_ext_schema={glib_ext_schema}, type is {type(glib_ext_schema)}')
    detected = []
    print( f'\nInstallations made to {GLIB2_SCHEMAS}:')
    for ext in INSTALLED_GSEXTENSIONS:
        ename = ext[ :ext.index('@') ]
        detected = [x for x in glib_ext_schema if ename in x ]
        #print( f'ename={ename} detected={detected}' )
        if detected:
            print( f' Checked: {ename:<30} ---> {detected[0]}' )
        if not detected:
            print( f' Checked: {ename:<30} ---> No Schema.' )


def install_theme_font_or_gsextension( url, dst ):
    '''Function to install a Gnome-shell theme, font or extension from a given "url" to a destination folder "dst".'''

    def get_gsextension_uuid( file ):
        '''Get UUID from the metadata of a GNOME shell extension. \
           "file" must be a zipfile.ZipFile object. '''
        with file.open( "metadata.json" ) as metadata:
            json_data = jsonloads( metadata.read() )
            gsextension_uuid = json_data["uuid"]
            return gsextension_uuid

    #print( f'\nProcess {os.getpid()} {current_thread()}  Installing {os.path.basename(url)}' )
    response = get_url_response( url )
    if 'zip' in url:
        #print( f'zip file { os.path.basename(url)} detected.' )
        with ZipFile( BytesIO( response.read() ) ) as zfile:
            if 'extensions.gnome.org' in url:
                uuid = get_gsextension_uuid( zfile )
                #print( 'uuid = ', uuid )
                destination = dst / uuid
                if destination.is_dir():
                    rmtree( destination )
                zfile.extractall( path=destination )
                output = uuid
                copy_gs_extensions_schema_to_glib2_schemas( uuid )
                run( f'gnome-shell-extension-tool -e {uuid}', shell=True )
            else:
                zfile.extractall( path=dst )
                folder = Path( url )
                if folder.name in 'macfonts.zip':
                    output = 'macfonts.zip'
                else:
                    output = folder.parents[1].name + '-' + folder.name
    else:
        response.close()
        raise ValueError( f'Extension must have a ".zip" url.' )
    
    response.close()
    #print( f'Process {os.getpid()} {current_thread()}  Installing {os.path.basename(url)} is completed. \n-->output={output}' )
    return output


def get_url_response( url ):
    req = Request( url )
    try:
        response = urlopen( req )
    except URLError as e:
        if hasattr( e, 'reason' ):
            print( 'We failed to reach a server.' )
            print( 'Reason: ', e.reason )
    else:
        # everything is fine
        #print( 'response obtained.', url)
        #print( 'response.geturl()')
        #print( 'response.info()')
        #print( 'response.getcode()')
        return response


def copy_gs_extensions_schema_to_glib2_schemas( uuid ):
    '''Copy schema_in_extension to schema_in_glib_schema, and compiles glib schemas.'''
    # Get schema of extension
    try:
        ext_schema_path = Path( next( Path( f'{GSEXTENSIONS}/{uuid}/schemas' ).glob('*.gschema.xml') ) )
    except StopIteration:
        pass
    else:
        ext_schema_name = ext_schema_path.name                 # Get schema name
        ext_glib_schema_path = GLIB2_SCHEMAS / ext_schema_name # Create schema's path to glib_2.0/schemas directory
        copy2( ext_schema_path, ext_glib_schema_path )         # Copy schema to glib_2.0/schemas directory


def configure_GNOME_Shell_extensions():
    print( '\nConfiguring GNOME Shell Extensions ...' )
    
    # 1. Configure GS Extensions installed with sudo permission
    root_gsexts = '/usr/share/gnome-shell/extensions/'
    if Path( root_gsexts + 'user-theme@gnome-shell-extensions.gcampax.github.com' ).exists():
        configure_user_theme()
    if Path( root_gsexts + 'dash-to-dock@micxgx.gmail.com' ).exists():
        configure_dash_to_dock()
    if Path( root_gsexts + 'ubuntu-dock@ubuntu.com' ).exists():
        configure_ubuntu_dock()
    
    # 2. Configure GS Extensions installed with user permission
    config_extensions = { 'arc-menu'                  :configure_arc_menu,
                          'blyr'                      :configure_blyr,
                          'dynamic-panel-transparency':configure_dynamic_panel_transparency,
                          'EasyScreenCast'            :configure_EasyScreenCast,
                          'netspeed'                  :configure_netspeed,
                          'suspend-button'            :configure_suspend_button,
                          #'user-theme'                :configure_user_theme,
                          }
    #print( 'INSTALLED_GSEXTENSIONS = ', INSTALLED_GSEXTENSIONS, 'len=', len(INSTALLED_GSEXTENSIONS) )
    #INSTALLED_GSEXTENSIONS = [ 'alwayszoomworkspaces@jamie.thenicols.net',
    #                           'arc-menu@linxgem33.com',
    #                           'blyr@yozoon.dev.gmail.com',
    #                           'dynamic-panel-transparency@rockon999.github.io',
    #                           'EasyScreenCast@iacopodeenosee.gmail.com',
    #                           'gnome-shell-screenshot@ttll.de',
    #                           'LogOutButton@kyle.aims.ac.za',
    #                           'netspeed@hedayaty.gmail.com',
    #                           'suspend-button@laserb',
    #                           ]
    inext = [ ext[:ext.index('@')] for ext in INSTALLED_GSEXTENSIONS ]
    #print( inext )
    if 'arc-menu' in inext:
        config_extensions['arc-menu']()
    if 'blyr' in inext:
        config_extensions['blyr']()
    if 'dynamic-panel-transparency' in inext:
        config_extensions['dynamic-panel-transparency']()
    if 'EasyScreenCast' in inext:
        config_extensions['EasyScreenCast']()
    if 'netspeed' in inext:
        config_extensions['netspeed']()
    if 'suspend-button' in inext:
        config_extensions['suspend-button']()
    print( '\nConfiguring GNOME Shell Extensions ... Done.' )
       

def gsettings_set( schema, keys_values ):
    '''Mimics bash "gsettings set" command. 

    Arguments:
    - "schema" is a string object.
    - "keys_values" is a list object containing pairs of key and value that are encased in a list.
    '''
    for kv in keys_values:
        try:
            cmd = f'gsettings set {schema} {kv[0]} {kv[1]}'
            print( f' {cmd}' )
            run( cmd, shell=True, encoding='utf8', check=True,)
        except Exception as exc:
            print(exc)


def configure_user_theme():
    print( '\n Configuring user-theme ...' )
    gsettings_set( 'org.gnome.shell.extensions.user-theme', [ ['name','Sierra-light'] ] )
    print( ' Configuring user-theme ... Done.' )


def configure_dash_to_dock():
    print( '\n Configuring dash-to-dock ...' )
    #1. Reset to default
    run( [ 'dconf', 'reset', '-f', '/org/gnome/shell/extensions/dash-to-dock' ], stdout=sys.stdout )

    #2. Customise
    schema = 'org.gnome.shell.extensions.dash-to-dock'
    keys_values = [
        ['click-action', '\'minimize\'' ],                  #Minimize window when it's icon is clicked
        ['middle-click-action', '\'previews\''],          #Show preview of opened App windows with mouse middle-button/wheel click
        ['custom-theme-customize-running-dots', 'false'], #Use Custom Dock Indicator
        ['custom-theme-shrink', 'false' ],                #Disable Custom Dock Shrink
        ['dock-fixed', 'true' ],                          #Dock always visible
        ['dock-position', '\'BOTTOM\'' ],                 #Re-Position Dock to Bottom
        ['extend-height', 'false' ],                      #Disable Extend height
        ['show-apps-at-top', 'true' ],                    #Show Apps button at left end of dock
        ['transparency-mode', '\'FIXED\'' ],                #Change Dock Transparency mode
        ['background-opacity', '0.2' ],                   #Set Dock Opacity to 20%
        ]
    gsettings_set( schema, keys_values )
    print( ' Configuring dash-to-dock ... Done.' )

 
def configure_ubuntu_dock():
    print( '\n Configuring ubuntu-dock ...' )
    # To remove it and yet be able to reinstall it without causing too much system changes,
    #  a known method is to rename it's folder with a backup extension. 
    ubuntu_dock = '/usr/share/gnome-shell/extensions/ubuntu-dock@ubuntu.com'
    if Path( ubuntu_dock ).exists():
        run( f'sudo mv {ubuntu_dock} {ubuntu_dock+".bak"}', shell=True)
    print( ' Configuring ubuntu-dock ... Done.' )


def configure_arc_menu():
    print( '\n Configuring arc-menu ...' )
    #1. Reset to default
    run( [ 'dconf', 'reset', '-f', '/org/gnome/shell/extensions/arc-menu' ],
         stdout=sys.stdout )

    #2. Get user-theme name
    theme = run( [ 'gsettings', 'get', 'org.gnome.shell.extensions.user-theme',
                   'name' ], stdout=PIPE ).stdout.decode().rstrip()

    #3. Get icon corresponding to theme
    url = 'https://assets.ubuntu.com/v1/9fbc8a44-circle-of-friends-web.zip'
    sl = Path( '/usr/share/themes/Sierra-light/gnome-shell/assets/activities.svg' )
    sd = Path( '/usr/share/themes/Sierra-dark/gnome-shell/assets/activities.svg' )
    response = get_url_response( url )
    if 'zip' in url:
        #print( f'zip file { os.path.basename(url)} detected.' )
        with ZipFile( BytesIO( response.read() ) ) as zfile:
            try:
                #print( zfile.namelist() )
                zfile.extract( 'circle-of-friends-web/PNG/cof_orange_hex.png',
                               path=ICONS )
            except Exception:
                if theme in 'Sierra-light':
                    src = sl
                elif theme in 'Sierra-dark':
                    src = sd
            else:
                src = ICONS/'circle-of-friends-web'/'PNG'/'cof_orange_hex.png'
    else:
        if theme in 'Sierra-light':
            src = sl
        elif theme in 'Sierra-dark':
            src = sd

    #4. Configure Arc-menu 
    schema = 'org.gnome.shell.extensions.arc-menu'
    keys_values = [
        ['custom-menu-button-icon', src],        #Location of custom icon 
        ['menu-button-icon', 'Custom_Icon'],     #Use "Custom Icon"
        ['custom-menu-button-text', '"Ubuntu"'], #Text next to custom icon 
        ]
    gsettings_set( schema, keys_values )
    print( ' Configuring arc-menu ... Done.' )


def configure_blyr():
    print( '\n Configuring blyr ...' )
    #1. Reset to default
    run( [ 'dconf', 'reset', '-f', '/org/gnome/shell/extensions/blyr' ], stdout=sys.stdout )

    #2. Customise
    schema = 'org.gnome.shell.extensions.blyr'
    keys_values = [ ['activitiesbrightness', '0.91'] ]
    gsettings_set( schema, keys_values )
    print( ' Configuring blyr ... Done.' )


def configure_dynamic_panel_transparency():
    pass # implement if needed


def configure_EasyScreenCast():
    pass # implement if needed


def configure_netspeed():
    pass # implement if needed


def configure_suspend_button():
    pass # implement if needed


def configure_Desktop():
    print( '\nConfiguring Desktop ...' )
    configure_Desktop_Interface()
    configure_Desktop_Calender()
    configure_Desktop_Datetime()
    configure_Desktop_Privacy()
    print( '\nConfiguring Desktop ... Done' )


def configure_Desktop_Interface():
    print( '\n Configuring Desktop Interface ...' )
    schema = 'org.gnome.desktop.interface'
    keys_values = [
        ['gtk-theme', 'Sierra-light'],                                 #GNOME Tweaks -> Appearance -> Application
        ['cursor-theme', 'MacOSMOD-master'],                           #GNOME Tweaks -> Appearance -> Cursor
        ['icon-theme', 'Cupertino-Catalina-iCons-master'],             #GNOME Tweaks -> Appearance -> Icon   
        ['font-name', '\'San Francisco Display Regular 12\''],         #GNOME Tweaks -> Fonts -> Interface
        ['document-font-name', '\'San Francisco Display Regular 11\''],#GNOME Tweaks -> Fonts -> Document
        ['monospace-font-name', '\'Ubuntu Mono 13\''],                 #GNOME Tweaks -> Fonts -> Monospace
        ['clock-format', '12h'],
        ['clock-show-date', 'true'],
        ['clock-show-seconds', 'true'],
        ]
    gsettings_set( schema, keys_values )
    print( ' Configuring Desktop Interface ... Done.' )


def configure_Desktop_Calender():
    print( '\n Configuring Desktop Calendar ...' )
    schema = 'org.gnome.desktop.calendar'
    keys_values = [ ['show-weekdate', 'true'] ]
    gsettings_set( schema, keys_values )
    print( ' Configuring Desktop Calendar ... Done.' )


def configure_Desktop_Datetime():
    print( '\n Configuring Desktop Datetime ...' )
    schema = 'org.gnome.desktop.datetime'
    keys_values = [ ['automatic-timezone', 'true'] ]
    gsettings_set( schema, keys_values )
    print( ' Configuring Desktop Datetime ... Done.' )


def configure_Desktop_Privacy():
    print( '\n Configuring Desktop Privacy ...' )
    #1. Reset to default
    run( [ 'dconf', 'reset', '-f', '/org/gnome/desktop/privacy' ],
         stdout=sys.stdout )
    #2. Set Values
    schema = 'org.gnome.desktop.privacy'
    keys_values = [
        ['remember-recent-files', 'true'],  #Settings -> Privacy -> Usage & History -> Recently Used -> ON
        ['remove-old-temp-files', 'true'],  #Settings -> Privacy -> Purge Trash & Temporary Files -> Automatically empty Temporary Files -> ON
        ['remove-old-trash-files', 'true'], #Settings -> Privacy -> Purge Trash & Temporary Files -> Automatically empty Trash -> ON   
        ]
    gsettings_set( schema, keys_values )
    print( ' Configuring Desktop Privacy ... Done.' )


def configure_Window_Manager_Preferences():
    print( '\nConfiguring Window Manager Preferences ...' )
    schema = 'org.gnome.desktop.wm.preferences'
    keys_values = [
        ['titlebar-font', '\'San Francisco Display Medium 12\''], #GNOME Tweaks --> Fonts --> Window Title
        #['button-layout', '\'close,minimize,maximize:\''],        #Uncomment for Left Placement (Same as Mac OS )
        ['button-layout', '\':minimize,maximize,close\''],        #Uncomment for Right Placement (Same as Ubuntu )
        ]
    gsettings_set( schema, keys_values )
    print( 'Configuring  Window Manager Preferences ... Done.' )


def configure_Applications():
    print( '\nConfiguring Applications ...' )
    configure_gnome_terminal()
    configure_libreoffice()
    configure_nautilus()
    install_nautilus_script_Revamp_Wallpaper()
    print( '\nConfiguring Applications ... Done.' )


def configure_gnome_terminal():
    print( '\n Configuring gnome-terminal ...' )
    #1. Get Profile uuid
    uuid = run( ['gsettings', 'get', 'org.gnome.Terminal.ProfilesList', 'default'],
                stdout=PIPE, encoding="utf-8" ).stdout.replace("'", "").rstrip()
    schema = f'org.gnome.Terminal.Legacy.Profile:/org/gnome/terminal/legacy/profiles:/:{uuid}/'
    #2. Make changes to gnome-terminal --> Edit --> Preference --> profile --> color
    keys_values = [
        ['use-theme-colors', 'false'],                #Deselect "use transparency from system theme"
        ['foreground-color', '\'rgb(211,215,207)\''], #Select Built-in schemes = Tango dark
        ['background-color', '\'rgb(46,52,54)\''],    #Select Built-in schemes = Tango dark
        ['use-theme-transparency', 'false'],          #Deselect "use color from system theme"
        ['use-transparent-background', 'true'],       #Select "use transparent background"
        ['background-transparency-percent', 38 ],     #Set value of "use transparent background"
        ]
    gsettings_set( schema, keys_values )
    print( ' Configuring gnome-terminal ... Done.' )


def configure_libreoffice():
    print( '\n Configuring libreoffice ...' )
    
    def symbolstyle_phrase( style ):
        return f'"SymbolStyle" oor:op="fuse"><value>{style}</value></prop></item>'

    lbxcu = HOME/'.config'/'libreoffice'/'4'/'user'/'registrymodifications.xcu'
    symbolstyles = [ 'auto', 'sifr_dark', 'tango', 'breeze', 'galaxy', 'breeze_dark' ]
    if lbxcu.exists():
        backup = Path( str(lbxcu) + '.bak' )
        if not backup.exists(): #Do not replace if registrymodifications.xcu.bak exists.
            copy2( lbxcu, backup )
        with open( lbxcu, 'r' ) as file:
            filedata = file.read()
        for style in symbolstyles:
            phrase = symbolstyle_phrase(style)
            if filedata.find( phrase ) != -1: #detected phrase
                filedata = filedata.replace( phrase, symbolstyle_phrase('sifr') ) #replace phrase
                break
        with open( lbxcu, 'w' ) as file:
            file.write( filedata )
        print( ' Configuring libreoffice ... Done.' )
    else:
        print( ' Configuring libreoffice ... Not Done.' )
    

def configure_nautilus():
    print( '\n Configuring nautilus ...' )
    schema = 'org.gnome.nautilus.preferences'
    keys_values = [
        ['click-policy', '\'single\''], #Single left mouse click to launch/open files
        ]
    gsettings_set( schema, keys_values )
    print( ' Configuring nautilus ... Done.' )
    

def install_nautilus_script_Revamp_Wallpaper():
    print( '\n Installing nautilus script "Revamp Wallpaper" ...' )
    src = INSTALLER_DIR / Path('resources/nautilus/Revamp Wallpaper')
    dst = HOME / Path('.local/share/nautilus/scripts/Revamp Wallpaper')
    copy2( src, dst )
    dst.chmod(0o771)    
    print( ' Installing nautilus script "Revamp Wallpaper" ... Done.' )

    
def configure_Desktop_and_Lockscreen_Wallpaper():
    print( '\nConfiguring Desktop Wallpaper and Screensaver...' )
    #1. Unzip and extractall images to BACKGROUNDS
    with ZipFile( INSTALLER_DIR / Path('resources/backgrounds/Sierra-wallpapers.zip' ), 'r' ) as zfile:
       zfile.extractall( BACKGROUNDS )

    #2. Configure desktop wallpaper
    sierra = BACKGROUNDS / Path('Sierra-wallpapers/Sierra2.jpg')
    wallpaper = BACKGROUNDS/'wallpaper.jpg'
    copy2( sierra, wallpaper )
    #run( f'gsettings set org.gnome.desktop.background picture-uri file://{wallpaper}',
    gsettings_set( 'org.gnome.desktop.background', [ ['picture-uri', f'\'{wallpaper.as_uri()}\''] ] )

    #3. Configure screensaver wallpaper, i.e. GDM lockscreen
    lockscreen = BACKGROUNDS/'lockscreen.jpg'
    run( ['convert', '-resize', '1440', '-quality', '100', '-brightness-contrast',
          '-10x-15', '-blur', '0x30', wallpaper, lockscreen], stdout=sys.stdout )
    gsettings_set( 'org.gnome.desktop.screensaver', [ ['picture-uri', f'\'{lockscreen.as_uri()}\''] ] )

    #4. Allow GNOME Wallpaper Picker access to "wallpaper" and "lockscreen"
    src = INSTALLER_DIR/ Path('resources/gnome-background-properties/revamp-wallpapers.xml')
    xml = GBACKGROUNDS_PROPERTIES/'revamp-wallpapers.xml'
    copy2( src, xml )
    print( 'Configuring Desktop Wallpaper and Screensaver... Done.' )


def configure_GDM():
    print( '\nConfiguring GNOME Display Manager (GDM) ...' )
    #1. Install revamp1804.css and its files
    installer_css = INSTALLER_DIR / Path('resources/gnome-shell_theme/Revamp1804/revamp1804.css')
    print( f'installer_css = {installer_css}' )
    run( [ 'sudo', 'python3.6', str( INSTALLER_DIR / 'gdm3css.py' ),
           '--install', str( installer_css ) ] )
    
    print( 'Configuring GNOME Display Manager (GDM) ... Done' )

    
def show_remove_statement():
    print()
    print( f'\n                           REMOVING REVAMP.....\n' )


def reset_GDM():
    print( '\nResetting GNOME Display Manager (GDM) ...' )
    #1. Remove revamp1804.css and its files and put back ubuntu.css
    css = Path('/usr/share/gnome-shell/theme/Revamp1804/revamp1804.css')
    run( [ 'sudo', 'python3.6', str( INSTALLER_DIR / 'gdm3css.py' ),
           '--remove', str( css ) ] )
    print( 'Resetting GNOME Display Manager (GDM) ... Done' )

    
def reset_Desktop_and_Lockscreen_Wallpaper():
    print( '\n  Resetting Desktop Wallpaper and Screensaver...' )
    #1. Reset desktop wallpaper
    warty = Path( '/usr/share/backgrounds/warty-final-ubuntu.png' )
    warty_src = INSTALLER_DIR /  Path( 'resources/backgrounds/warty-final-ubuntu.png' )
    warty_dst = BACKGROUNDS / 'warty-final-ubuntu.png'
    if not warty.exists():
        copy2( warty_src, warty_dst )
        wallpaper = warty_dst
    else:
        wallpaper = warty
    #run( f'gsettings set org.gnome.desktop.background picture-uri file://{wallpaper}',
    gsettings_set( 'org.gnome.desktop.background', [ ['picture-uri', f'\'{wallpaper.as_uri()}\''] ] )

    #2. Reset screensaver wallpaper, i.e. GDM lockscreen
    wartygrey = Path( '/usr/share/backgrounds/Beaver_Wallpaper_Grey_4096x2304.png' )
    wartygrey_src = INSTALLER_DIR /  Path( 'resources/backgrounds/Beaver_Wallpaper_Grey_4096x2304.png' )
    wartygrey_dst = BACKGROUNDS / 'Beaver_Wallpaper_Grey_4096x2304.png'
    if not wartygrey.exists():
        copy2( wartygrey_src, wartygrey_dst )
        lockscreen = wartygrey_dst
    else:
        lockscreen = wartygrey
    gsettings_set( 'org.gnome.desktop.screensaver', [ ['picture-uri', f'\'{lockscreen.as_uri()}\''] ] )

    #3. Allow GNOME Wallpaper Picker access to "wallpaper" and "lockscreen"
    src = INSTALLER_DIR/ Path('resources/gnome-background-properties/ubuntu-wallpapers.xml')
    xml = GBACKGROUNDS_PROPERTIES/'ubuntu-wallpapers.xml'
    copy2( src, xml )

    #4. Remove revamp files & folders
    rmtree( BACKGROUNDS / 'Sierra-wallpapers' )
    lockscreen = BACKGROUNDS / 'lockscreen.jpg'
    wallpaper = BACKGROUNDS / 'wallpaper.jpg'
    lockscreen.unlink()
    wallpaper.unlink()
    print( '  Resetting Desktop Wallpaper and Screensaver... Done.' )


def reset_Applications():
    print( '\nResetting Applications ...' )
    remove_nautilus_script_Revamp_Wallpaper()
    reset_nautilus()
    reset_libreoffice()
    reset_gnome_terminal()
    print( '\nResetting Applications ... Done.' )


def remove_nautilus_script_Revamp_Wallpaper():
    print( '\n  Removing nautilus script "Revamp Wallpaper" ...' )
    dst = HOME / Path('.local/share/nautilus/scripts/Revamp Wallpaper')
    dst.unlink()
    print( '  Removing nautilus script "Revamp Wallpaper" ... Done.' )


def reset_nautilus():
    print( '\n  Resetting nautilus ...' )
    schema = 'org.gnome.nautilus.preferences'
    keys_values = [
        ['click-policy', '\'double\''], #Double left mouse click to launch/open files
        ]
    gsettings_set( schema, keys_values )
    print( '  Resetting nautilus ... Done.' )
    

def reset_libreoffice():
    print( '\n  Resetting libreoffice ...' )
    def newphrasesymbolstyle( style ):
        return f'"SymbolStyle" oor:op="fuse"><value>{style}</value></prop></item>'

    lbxcu = HOME/'.config'/'libreoffice'/'4'/'user'/'registrymodifications.xcu'
    symbolstyles = [ 'sifr', 'sifr_dark', 'tango', 'breeze', 'galaxy', 'breeze_dark' ]
    if lbxcu.exists():
        with open( lbxcu, 'r' ) as file:
            filedata = file.read()
        for style in symbolstyles:
            print( f'style = {style}, {type(style)} ' )
            old = newphrasesymbolstyle(style)
            print( f'old = {old} ' )
            if filedata.find( old ):
                print( 'Found ', old )
                filedata = filedata.replace( old, newphrasesymbolstyle('auto') )
                break
            else:
                print('  Did not replace style to "auto".')
        with open( lbxcu, 'w' ) as file:
            file.write( filedata )
        print( '  Resetting libreoffice ... Done.' )
    else:
        print( '  Resetting libreoffice ... Not Done.' )
    

def reset_gnome_terminal():
    print( '\n  Resetting gnome-terminal ...' )
    #1. Get profile uuid
    uuid = run( ['gsettings', 'get', 'org.gnome.Terminal.ProfilesList', 'default'],
                stdout=PIPE, encoding="utf-8" ).stdout.replace("'", "").rstrip()
    schema = f'org.gnome.Terminal.Legacy.Profile:/org/gnome/terminal/legacy/profiles:/:{uuid}/'
    #2. Make changes to gnome-terminal --> Edit --> Preference --> profile --> color
    keys_values = [
        ['use-transparent-background', 'false'],      #Deselect "use transparent background"
        ['use-theme-transparency', 'true'],           #Select "use color from system theme"
        ['use-theme-colors', 'true'],                #Deselect "use transparency from system theme"
        ]
    gsettings_set( schema, keys_values )
    print( '  Resetting gnome-terminal ... Done.' )


def reset_Window_Manager_Preferences():
    print( '\nResetting Window Manager Preferences ...' )
    #1. Reset to default
    run( [ 'dconf', 'reset', '-f', '/org/gnome/desktop/wm/preferences' ],
         stdout=sys.stdout )

    #2. Configure to Ubuntu
    schema = 'org.gnome.desktop.wm.preferences'
    keys_values = [
        ['titlebar-font', '\'Ubuntu Bold 11\''],             #GNOME Tweaks --> Fonts --> Window Title
        #['button-layout', '\'close,minimize,maximize:\''],  #Uncomment for Left Placement (Same as Mac OS )
        ['button-layout', '\':minimize,maximize,close\''],   #Uncomment for Right Placement (Same as Ubuntu )
        ]
    gsettings_set( schema, keys_values )
    print( 'Resetting  Window Manager Preferences ... Done.' )


def reset_Desktop():
    print( '\nResetting Desktop ...' )
    reset_Desktop_Interface()
    reset_Desktop_Calender()
    reset_Desktop_Datetime()
    reset_Desktop_Privacy()
    print( '\nResetting Desktop ... Done' )


def reset_Desktop_Interface():
    print( '\n  Resetting Desktop Interface ...' )
    schema = 'org.gnome.desktop.interface'
    keys_values = [
        ['gtk-theme', '\'Ambiance\''],                #GNOME Tweaks -> Appearance -> Application
        ['cursor-theme', '\'DMZ-White\''],            #GNOME Tweaks -> Appearance -> Cursor
        ['icon-theme', '\'ubuntu-mono-dark\''],       #GNOME Tweaks -> Appearance -> Icon   
        ['font-name', '\'Ubuntu 11\''],               #GNOME Tweaks -> Fonts -> Interface
        ['document-font-name', '\'Sans 11\''],        #GNOME Tweaks -> Fonts -> Document
        ['monospace-font-name', '\'Ubuntu Mono 13\''],#GNOME Tweaks -> Fonts -> Monospace
        ['clock-format', '24h'],
        ['clock-show-date', 'false'],
        ['clock-show-seconds', 'false'],
        ]
    gsettings_set( schema, keys_values )
    print( '  Resetting Desktop Interface ... Done.' )


def reset_Desktop_Calender():
    print( '\n  Resetting Desktop Calendar ...' )
    schema = 'org.gnome.desktop.calendar'
    keys_values = [ ['show-weekdate', 'false'] ]
    gsettings_set( schema, keys_values )
    print( '  Resetting Desktop Calendar ... Done.' )


def reset_Desktop_Datetime():
    print( '\n  Resetting Desktop Datetime ...' )
    schema = 'org.gnome.desktop.datetime'
    keys_values = [ ['automatic-timezone', 'false'] ]
    gsettings_set( schema, keys_values )
    print( '  Resetting Desktop Datetime ... Done.' )


def reset_Desktop_Privacy():
    print( '\n  Resetting Desktop Privacy ...' )
    #1. Reset to default
    run( [ 'dconf', 'reset', '-f', '/org/gnome/desktop/privacy' ],
         stdout=sys.stdout )
    #2. Set Values
    schema = 'org.gnome.desktop.privacy'
    keys_values = [
        ['remember-recent-files', 'true'],  #Settings -> Privacy -> Usage & History -> Recently Used -> ON
        ['remove-old-temp-files', 'false'],  #Settings -> Privacy -> Purge Trash & Temporary Files -> Automatically empty Temporary Files -> ON
        ['remove-old-trash-files', 'false'], #Settings -> Privacy -> Purge Trash & Temporary Files -> Automatically empty Trash -> ON   
        ]
    gsettings_set( schema, keys_values )
    print( '  Resetting Desktop Privacy ... Done.' )


def reset_GNOME_Shell_extensions():
    print( '\nResetting GNOME Shell Extensions ...' )
    # 1. Reset GS Extensions installed with sudo permission
    root_gsexts = '/usr/share/gnome-shell/extensions/'
    if Path( root_gsexts + 'user-theme@gnome-shell-extensions.gcampax.github.com' ).exists():
        reset_user_theme()
    if Path( root_gsexts + 'dash-to-dock@micxgx.gmail.com' ).exists():
        reset_dash_to_dock()
    if Path( root_gsexts + 'ubuntu-dock@ubuntu.com.bak' ).exists():
        reset_ubuntu_dock()
    print( '\nResetting GNOME Shell Extensions ... Done.' )
       

def reset_user_theme():
    print( '\n Resetting user-theme ...' )
    gsettings_set( 'org.gnome.shell.extensions.user-theme', [ ['name','\'\''] ] )
    print( ' Resetting user-theme ... Done.' )


def reset_dash_to_dock():
    print( '\n Resetting dash-to-dock ...' )
    #1. Reset to default
    run( [ 'dconf', 'reset', '-f', '/org/gnome/shell/extensions/dash-to-dock' ], stdout=sys.stdout )

    #2. Customise
    schema = 'org.gnome.shell.extensions.dash-to-dock'
    keys_values = [
        ['click-action', '\'previews\'' ],              #Preview window when it's icon is clicked
        ['middle-click-action', '\'launch\''],          #Launch App window with mouse middle-button/wheel click
        ['custom-theme-customize-running-dots', 'true'],#Use Custom Dock Indicator
        ['custom-theme-shrink', 'true' ],               #Enable Custom Dock Shrink
        ['dock-fixed', 'true' ],                        #Dock always visible
        ['dock-position', '\'LEFT\'' ],                 #Position Dock to Left
        ['extend-height', 'true' ],                     #Enable Extend height
        ['show-apps-at-top', 'false' ],                 #Show Apps button at right end of dock
        ['transparency-mode', '\'ADAPTIVE\'' ],         #Adaptive  Dock Transparency mode
        ['background-opacity', '0.8' ],                 #Set Dock Opacity to 80% (default)
        ]
    gsettings_set( schema, keys_values )
    print( ' Resetting dash-to-dock ... Done.' )

 
def reset_ubuntu_dock():
    print( '\n Resetting ubuntu-dock ...' )
    # Convert ubuntu-dock@ubuntu.com.bak to ubuntu-dock@ubuntu.com. 
    ubuntu_dock = Path('/usr/share/gnome-shell/extensions/ubuntu-dock@ubuntu.com.bak')
    if ubuntu_dock.exists():
        run( f'sudo mv { str( ubuntu_dock ) } { str( ubuntu_dock.parent / ubuntu_dock.stem ) }', shell=True)
    print( ' Resetting ubuntu-dock ... Done.' )


def remove_themes_fonts_gsextensions():
    print( f'\nRemoving Themes, Fonts and Extensions ...' )
    #1. Only enable dash-to-dock gnome-shell extension
    revamp = { 'alwayszoomworkspaces@jamie.thenicols.net',
               'arc-menu@linxgem33.com',
               'blyr@yozoon.dev.gmail.com',
               'dynamic-panel-transparency@rockon999.github.io',
               'EasyScreenCast@iacopodeenosee.gmail.com',
               'gnome-shell-screenshot@ttll.de',
               'LogOutButton@kyle.aims.ac.za',
               'netspeed@hedayaty.gmail.com',
               'suspend-button@laserb',
               'workspace-indicator@gnome-shell-extensions.gcampax.github.com',
               'drive-menu@gnome-shell-extensions.gcampax.github.com',
               'user-theme@gnome-shell-extensions.gcampax.github.com'}
    
    schema = 'org.gnome.shell'
    keys_values = [
        [ 'enabled-extensions', '[]' ]
        ] 
    gsettings_set( schema, keys_values )
    print( f'  Only enable dash-to-dock gnome-shell extension.' )

    #2. Remove Fonts
    local_fonts = [ 'macfonts', 'SanFranciscoFont-master', '.uuid' ]
    for lf in local_fonts:
        font = FONTS / lf
        if font.is_dir():
            rmtree( font )
            print( f'   - removed {font}' )
        elif font.is_file():
            font.unlink()
            print( f'   - removed {font}' )
    print( f'  Removed installed fonts' )

    #3. Remove Icons
    local_icons = [ 'circle-of-friends-web',
                    'Cupertino-Catalina-iCons-master',
                    'Cupertino-iCons-master',
                    'MacOSMOD-master' ]
    for li in local_icons:
        icon = ICONS / li
        if icon.is_dir():
            rmtree( icon )
            print( f'   - removed {icon}' )
    print( f'  Removed installed icons' )

    #4. Remove gnome-shell extension schemas
    local_gschemas = [
        'gschemas.compiled',
        'org.gnome.shell.extensions.arc-menu.gschema.xml',
        'org.gnome.shell.extensions.blyr.gschema.xml',
        'org.gnome.shell.extensions.dynamic-panel-transparency.gschema.xml',
        'org.gnome.shell.extensions.easyscreencast.gschema.xml',
        'org.gnome.shell.extensions.netspeed.gschema.xml',
        'org.gnome.shell.extensions.screenshot.gschema.xml',
        'org.gnome.shell.extensions.suspend-button.gschema.xml',
        ]
    for i in local_gschemas:
        gschema = GLIB2_SCHEMAS / i
        if gschema.is_file():
            gschema.unlink()
            print( f'   - removed {gschema}' )
    print( f'  Removed installed gschemas... Done' )
    
    #5. Remove gnome-shell extensions
    local_gsextensions = [
        'alwayszoomworkspaces@jamie.thenicols.net',
        'arc-menu@linxgem33.com',
        'blyr@yozoon.dev.gmail.com',
        'dynamic-panel-transparency@rockon999.github.io',
        'EasyScreenCast@iacopodeenosee.gmail.com',
        'gnome-shell-screenshot@ttll.de',
        'LogOutButton@kyle.aims.ac.za',
        'netspeed@hedayaty.gmail.com',
        'suspend-button@laserb',
        'workspace-indicator@gnome-shell-extensions.gcampax.github.com',
        ]
    for i in local_gsextensions:
        ext = GSEXTENSIONS / i
        if ext.is_dir():
            rmtree( ext )
            print( f'   - removed {ext}' )
    print( f'  Removed installed gnome-shell extensions... Done' )

    print( f'Removing Themes, Fonts and Extensions ... Done.' )
            
    
def reset_apt_repository():
    '''Function to remove 'ppa:dyatlov-igor/sierra-theme' from apt-repository.'''
    cmd = ['sudo', 'add-apt-repository', '-y', '--remove', PPA[0] ]
    runN( cmd )
    print( f'\napt-repository is up to date.' )
    

def restart_gnome_shell():
    print( '\nRestarting GNOME shell ...' )
    cmd = 'xdotool key "Alt+F2+r" && sleep 0.5 && xdotool key "Return"'
    time.sleep( 0.5 )
    run( cmd, shell=True, stdout=sys.stdout )
    print( 'Restarting GNOME shell ... Done.' )


def install():
    show_intro()
    apt_update()
    update_apt_repository()
    apt_dist_upgrade()
    install_apt_pkgs()
    #Install Chromium Broswer extension: GNOME Shell integration
    # Download themes, fonts and gnome-shell extensions and install them
    install_themes_fonts_gsextensions()
    configure_GNOME_Shell_extensions()
    configure_Desktop()
    configure_Window_Manager_Preferences()
    configure_Applications()
    configure_Desktop_and_Lockscreen_Wallpaper()
    configure_GDM()
    restart_gnome_shell()
    

def remove():
    show_intro()
    show_remove_statement()
    reset_GDM()
    reset_Desktop_and_Lockscreen_Wallpaper()
    reset_Applications()
    reset_Window_Manager_Preferences()
    reset_Desktop()
    reset_GNOME_Shell_extensions()
    remove_themes_fonts_gsextensions()
    restart_gnome_shell()
    remove_apt_pkgs()
    reset_apt_repository()
    apt_update()
    apt_dist_upgrade()
    

def install_chromium_extensions( url ):
    # To do.
    pass


def main():
    #1. Setup the argument parser 
    parser = argparse.ArgumentParser()

    #2. Define arguement
    parser.add_argument( '--install', action='store_true', help='toggles the installation of Revamp 18.04.' )
    parser.add_argument( '--remove', action='store_true', help='toggles the removal of Revamp 18.04.' )
    
    #3. Get the arguements
    args = parser.parse_args()
    #print( f'args.install = {args.install}' )#for debugging
    #print( f'args.remove  = {args.remove}' ) #for debugging

    #4. Set up the permissible operations from cmdline.
    if args.install:
        #print('INSTALL')
        #print( f'type(args.install) = {type(args.install)}' )
        install()
    elif args.remove:
        #print('REMOVED')
        remove()
    else:
        parser.print_help()
        print( '\nPlease use command syntax.' )

    
if __name__ == "__main__":
  main()


