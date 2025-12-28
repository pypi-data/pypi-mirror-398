function render({model, el}) {
    el.classList.add('list-widget'); // want top level for layout settings by python
    
    function updateDescription() {
        const desc = model.get('description');
        el.dataset.description = desc || '';
        el.classList.toggle('has-description', Boolean(desc));
    }

    function updateTabs() {
        const vert = model.get('vertical');
        el.classList.toggle('tabs', Boolean(!vert));
    }
    
    function createItem(opt) {
        const item = document.createElement('div');
        item.className = 'list-item';
        
        const [index, html] = opt; // Always expects a tuple (index, html)
        item.innerHTML = html;
        item.dataset.index = index; // Use index for identification
        
        if (index === model.get('index')) {
            item.classList.add('selected');
        }
        
        item.addEventListener('click', () => {
            const newIndex = parseInt(item.dataset.index);
            if (newIndex !== model.get('index')) {
                model.set('index', newIndex); // Update index on click
                model.save_changes();
            }
        });
        
        return item;
    }
    
    function updateList() {
        el.innerHTML = ''; // Clear the list
        model.get('_options').forEach((opt) => {
            el.appendChild(createItem(opt));
        });
    }

     function updateSelected(index) {
        el.childNodes.forEach(item => {
            item.classList.remove('selected');
            if (parseInt(item.dataset.index) === index) {
                item.classList.add('selected');
            }
        });
    }
    
    updateDescription();
    updateList();
    updateTabs();

     model.on('change:index', () => { // This is apparent internal change, without setting index, not intended to be used by user
        const index = model.get('index');
        updateSelected(index);
    });
    
    model.on('change:description', updateDescription);
    model.on('change:_options', updateList);
    model.on('change:vertical', updateTabs);

     // Intercept custom messages from the backend
    model.on('msg:custom', (msg) => {
        if (msg?.active >= 0) { // Mock active, not changing index, for TOC list
            updateSelected(msg.active); 
        }
    });
}

export default { render }