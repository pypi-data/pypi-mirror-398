function render({model, el}) {
    const btn = document.createElement('button');
    el.className = 'fs-btn ips-fs';
    btn.innerHTML = '<i class="fa fa-expand"></i>';
    btn.title = 'Toggle Fullscreen';

     btn.onclick = () => {
        const parent = el.parentElement;
        if (!document.fullscreenElement || document.fullscreenElement !== parent) {
            parent.requestFullscreen()
                .then(() => {
                    model.set('isfullscreen', true);
                    model.save_changes();
                })
                .catch(err => console.error('Failed to enter fullscreen:', err));
        } else {
            document.exitFullscreen()
                .then(() => {
                    model.set('isfullscreen', false);
                    model.save_changes();
                })
                .catch(err => console.error('Failed to exit fullscreen:', err));
        }
        updateButtonUI(btn, parent);
    };

     document.addEventListener('fullscreenchange', () => {
        const parent = el.parentElement;
        if (!parent) return; // Exit if parent is null
        const isFullscreen = parent === document.fullscreenElement;
        model.set('isfullscreen', isFullscreen);
        model.save_changes(); 
        updateButtonUI(btn, parent);
    });

     function updateButtonUI(button, parent) {
        const isFullscreen = parent === document.fullscreenElement;
        button.querySelector('i').className = `fa fa-${isFullscreen ? 'compress' : 'expand'}`;
        if (!parent) return; // Exit if parent is null
        parent.style.background = isFullscreen ? 'var(--bg1-color, var(--jp-widgets-input-background-color, inherit))' : 'unset';
    }

     el.appendChild(btn);
}

 export default { render };
