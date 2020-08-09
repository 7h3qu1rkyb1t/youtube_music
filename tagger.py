import eyed3


def Tag(filename):
    # This function changes songs title so it is better to use this at the end
    special_chars = ["(", "["]  # Used to strip unnecessory song info in the filename.
    song_tag = eyed3.load(filename)
    tag  = filename[:filename.rfind(".")]
    try:
        artist,title = tag.split("-", maxsplit=1)
    except ValueError:
        print("Couldn't get the artist name!!!")
        title = tag
        artist = None
    for char in special_chars:
        if char in title:
            title = title[:title.index(char)]
    title = title.strip()
    artist = artist.strip()
    song_tag.tag.title = title
    song_tag.tag.artist = artist
    song_tag.tag.save()
    try:
        # if song name isn't changed os error will occur
        song_tag.rename(title)
    except OSError:
        pass
    return title

