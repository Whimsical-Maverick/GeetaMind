function get_recommendation_by_emotion(emotion)
{
    fetch("/get-by-emotion",{
        method: "GET",
        headers: {
            'content-type': 'application/json',

        },
        body: JSON.stringify({'content': emotion})
    })
    .then(response => response.json())
    .then(data => {
        const output = document.getElementById('output')
        for(const verse of data.verses){
            const versebox = document.createElement('div')
            versebox.innerText = verse
            output.appendChild(versebox)
        }  
    })
}