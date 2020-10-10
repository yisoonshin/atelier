function validate()
{
    let code = document.querySelector('#passcode').value;
    if (code === '24601')
    {
        var image = document.getElementById('secret_img');
        image.src = "content/0.jpg";
        var player = document.getElementById('player');
        player.src = "https://www.youtube.com/embed/EvRtKMxc88Q";
    }

}