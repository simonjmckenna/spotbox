let isDragging = false;
let startY;
let startScrollTop;

function startDrag(e) {
    isDragging = true;
    startY = e.clientY;
    startScrollTop = document.getElementById('tracklist-grid').scrollTop;
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', stopDrag);
}

function drag(e) {
    if (!isDragging) return;
    const moveY = e.clientY - startY;
    document.getElementById('tracklist-grid').scrollTop = startScrollTop - moveY;
}

function stopDrag() {
    isDragging = false;
    document.removeEventListener('mousemove', drag);
    document.removeEventListener('mouseup', stopDrag);
}


async function loadPlaylistName() {
  try {
    const response = await fetch("/webapi/get_playlist");
    const data = await response.json();

    const playlist= document.getElementById("playlistname");

    playlist.innerHTML = `${data.name}`;
    
  } catch (err) {
    console.error(err);
  }
}
async function loadCreditData() {
  try {
    const response = await fetch("/webapi/get_credits");
    const data = await response.json();

    const credits= document.getElementById("credits");

    credits.innerHTML = ` - Credits: ${data.credits}`;
    
  } catch (err) {
    console.error(err);
  }
}

async function loadTrackListData() {
    try {
        const response = await fetch('/webapi/get_trackList');
        const data = await response.json();

        const grid = document.getElementById("tracklist-grid");

        console.error(data)

        data.forEach( item => {
            const card = document.createElement("div");
            card.className = "card";

            card.innerHTML = `
                <img src="${item.image}" alt="${item.title}">
                <div class="text">
                    <div class="title">${item.title}</div>
                    <div class="artist">${item.artist}</div>
                </div> 
            `;
            clickApiUrl=`/webapi/queue_track`;
            // Click → call Web API passing track id and length
            card.addEventListener("click", () => {
                fetch (clickApiUrl, {
                                    method: "POST",
                                    headers: { "Content-Type": "application/json" },
                                    body: JSON.stringify({ trackid: item.trackid , tracktime: item.length } )
                                    }
                ).catch(err => console.error(err));
                loadCreditData();
            });

            grid.appendChild(card);
        })
    }
    
    catch { 
        console.error("Load error:", err);
    }
}

async function loadNowPlayingData() {
  try {
    const response = await fetch("/webapi/getNowPlayingTrack");
    const data = await response.json();

    const title = document.getElementById("nowplaying-title");
    const artist = document.getElementById("nowplaying-artist");
    const image = document.getElementById("nowplaying-image");
    const queue = document.getElementById("nowplaying-queue");  

    title.innerHTML  = `${data.title}`;
    artist.innerHTML = `${data.artist}`;
    image.innerHTML  = `<img class="center-fit" src="${data.image}" alt="No image">`;
    queue.innerHTML = `Tracks Waiting: ${data.queueLen}`;    
  } catch (err) {
    console.error(err);
  }
}


const interval = setInterval(function() {
   loadCreditData();
   loadNowPlayingData();
 }, 10000);

loadPlaylistName();
loadTrackListData();

loadCreditData();
loadNowPlayingData();


