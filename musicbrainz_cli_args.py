"""
    Author: PythagoreanBeanMachine (PBM)
    Assignment: MSU CSC-360 Project
    Professor: Dr. Sengupta

    Dependencies: 
        Linux: cdparanoia, ffmpeg, lltag, metaflac, libdiscid
        PIP: musicbrainzngs, python-libdiscid

        Fonts: My machine uses iosevka & sazanami for fonts.
               In order for viewing foreign scripts/glyphs,
               be sure to have the appropriate fonts installed
               on your local system.

    Notes: I plan on possibly uploading this to GitHub and the AUR for usage
           by the general public once some additional CLI arguments are implemented.
           These would include specified storage locations, audio codecs, disc location,
           and whether or not to include cover art in the tagging.
"""


# imported libraries
import musicbrainzngs as mb
import libdiscid
import argparse
import sys
import os


# defining the cli flags
parser = argparse.ArgumentParser()
parser.add_argument('-a', '--audio-codec', help='audio codec for output files', type=str)
parser.add_argument('-o', '--output-directory', help='output path for the output files', type=str)
parser.add_argument('-c', '--cover-art', help='will attempt to embed the associated cover art', action='store_true')
args = parser.parse_args()

# Setup MusicBrainz client
mb.set_useragent('Antiquarian Backups', '1.0.0')

# get Username/Password
creds = open('credentials', 'r').read().split('\n')
mb.auth(creds[0], creds[1])

# Select the disc and retrieve the MusicBrainz discid
disc = libdiscid.read(device=u'/dev/sr0')
disc_id = disc.id

# Collect the valuable metadata information from the discid in the MusicBrainz CDDA database
try:
    results = mb.get_releases_by_discid(disc_id, includes=['artists', 'recordings'])
except mb.musicbrainz.ResponseError as re:
    print('Error retrieving the releases data, check if the Title has a discID on musicbrainz.org')
    sys.exit(1)

# save the releaseid
release_id = results['disc']['release-list'][0]['id']

disc_info = {}
tracks = []

# grab the track names of each song
for item in results['disc']['release-list'][0]['medium-list'][0]['track-list']:
    tracks.append(item['recording']['title'])

disc_info['tracks'] = tracks

# Grab the list containing the Album Title and Artist name
this_release = results['disc']['release-list'][0]

# append to disc_info variable for easy use
disc_info['title'] = this_release['title']
disc_info['artist'] = this_release['artist-credit'][0]['artist']['name']

# List the CD's tracks for the user see
print(f"Artist: {disc_info['artist']}\nAlbum: {disc_info['title']}\n\nTracks:")
for track in disc_info['tracks']:
    print(f"{disc_info['tracks'].index(track) + 1}) {track}")

# Check of the associated Artist/Album tree exists in the local file tree
# If not, then create where necessary
if args.output_directory:
    os.chdir(f'{args.output_directory}')
if not os.path.isdir(disc_info['artist']):
    os.mkdir(f"{disc_info['artist']}")
os.chdir(disc_info['artist'])
if not os.path.isdir(disc_info['title']):
    os.mkdir(disc_info['title'])
os.chdir(disc_info['title'])

# rip each track and convert to flac codec
# Bash equivilent of the upcoming os.system() call for comprehension
'''
cd paranoia -Bf
count=1
for i in $(ls)
do
    ffmpeg -i $i ${count}.flac
    ((count++))
done
rm *.aiff
'''
os.system('cdparanoia -Bf; count=1; for i in $(ls); do ffmpeg -i $i ${count}.flac && ((count++)); done; rm *.aiff')
songs = os.listdir()

# add the appropriate tags to each track, then rename each track to the track's album listing
for song in songs:
    os.system(f"lltag --yes -t '{disc_info['tracks'][int(song[:-5]) - 1]}' -a '{disc_info['artist']}' -A '{disc_info['title']}' -n '{int(song[:-5])}' --flac {song}")
    os.system(f"mv -v {song} '{disc_info['tracks'][int(song[:-5]) - 1]}'.flac")

# create a png image file of the front cover art
if args.cover_art:
    try:
        image = mb.get_image_front(release_id)
        with open('cover.png', 'wb') as file:
            file.write(image)

        # set the cover art as the tracks' picture value value
        os.system(f'metaflac --import-picture-from=cover.png *.flac')
        print('Applied cover art ...')
    except:
        print('No cover art found...')
        pass

# eject the CD from the optical drive
os.system('eject /dev/sr0')
