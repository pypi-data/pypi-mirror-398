function buildSrcsetLookup(srcsetAttribute) {
    let lookup = {};
    let srcsetParts = srcsetAttribute.split(',');

    srcsetParts.forEach(part => {
        let [url, widthDescriptor] = part.trim().split(/\s+/);
        if (widthDescriptor) {
            // Remove 'w' from the width descriptor if present
            let width = widthDescriptor.replace('w', '');
            lookup[width] = url;
        }
    });

    return lookup;
}


class ImageGallery extends HTMLElement {
	constructor () {
		super();
		console.log('Constructed', this);
        this.currentImage = null;
	}
    static register(tagName) {
        console.log("Registering image-gallery");
        if ("customElements" in window) {
            customElements.define(tagName || "image-gallery", ImageGallery);
        }
    }
    replaceImage (direction) {
        if (this.currentImage) {
            const which = this.currentImage.getAttribute(direction);
            if (which === "false") {
                return;
            }
            const targetElement = this.querySelector('#' + which)
            if (targetElement) {
                this.setModalImage(targetElement);
            }
        }
    }
    chooseFromSrcset(srcset) {
        const lookup = buildSrcsetLookup(srcset);
        const widths = Object.keys(lookup);
        widths.sort();
        // return the second biggest image
        return lookup[widths[2]];
    }
    prefetchImage(url) {
        if (url) {
            const img = new Image();
            img.src = url;
            // Optionally, you can add event listeners for 'load' and 'error' events
            // img.onload = () => console.log(`Image preloaded: ${url}`);
            // img.onerror = () => console.log(`Error preloading image: ${url}`);
        }
    }
    prefetchImageFromSrcSet(imageId) {
        const imageElement = this.querySelector(`#${imageId}`);
        const pictureElement = imageElement.parentNode;
        const sourceElement = pictureElement.querySelector('source');
        if (sourceElement) {
            const srcset = sourceElement.getAttribute('data-modal-srcset');
            if (srcset) {
                const url = this.chooseFromSrcset(srcset);
                console.log("prefetching: ", url);
                this.prefetchImage(url);
            }
        }
    }
    prefetchAdjacentImages(img) {
        const prevImageId = img.getAttribute('data-prev');
        const nextImageId = img.getAttribute('data-next');

        if (prevImageId && prevImageId !== 'false') {
            this.prefetchImageFromSrcSet(prevImageId);
        }

        if (nextImageId && nextImageId !== 'false') {
            this.prefetchImageFromSrcSet(nextImageId);
        }
    }
    setModalImage (img) {
        this.currentImage = img;
        const thumbnailPicture = img.parentNode;
        const fullUrl = thumbnailPicture.parentNode.getAttribute("data-full");
        const thumbnailSource = thumbnailPicture.querySelector('source');
        const modalBody = this.querySelector(".modal-body");
        const modalFooter = this.querySelector(".modal-footer");

        const sourceAttributes = [
            { attr: "data-modal-srcset", prop: "srcset" },
            { attr: "data-modal-src", prop: "src" },
            { attr: "type", prop: "type" },
            { attr: "data-modal-sizes", prop: "sizes" },
        ];

        const modalSource = modalBody.querySelector("source");
        for (const { attr, prop } of sourceAttributes) {
            const value = thumbnailSource.getAttribute(attr);
            if (value) {
                modalSource.setAttribute(prop, value);
            }
        }

        const imgAttributes = [
            { attr: "alt", prop: "alt" },
            { attr: "data-prev", prop: "data-prev" },
            { attr: "data-next", prop: "data-next" },
            { attr: "data-fullsrc", prop: "src" },
            { attr: "data-modal-srcset", prop: "srcset" },
            { attr: "data-modal-sizes", prop: "sizes" },
            { attr: "data-modal-height", prop: "height"},
            { attr: "data-modal-width", prop: "width"},
        ];

        const modalImage = modalBody.querySelector("img");
        modalImage.parentNode.parentNode.setAttribute("href", fullUrl);
        for (const { attr, prop } of imgAttributes) {
            const value = img.getAttribute(attr);
            if (value) {
                modalImage.setAttribute(prop, value);
            }
        }

        let buttons = ''
        // prev button
        const prev = modalImage.getAttribute('data-prev');
        if (prev !== "false") {
            buttons = buttons + '<button id="data-prev" type="button" class="btn btn-primary">Prev</button>'
        } else {
            buttons = buttons + '<button id="data-prev" type="button" class="btn btn-primary disabled">Prev</button>'
        }

        // next button
        const next = modalImage.getAttribute('data-next');
        if (next !== "false") {
            buttons = buttons + '<button id="data-next" type="button" class="btn btn-primary">Next</button>'
        } else {
            buttons = buttons + '<button id="data-next" type="button" class="btn btn-primary disabled">Next</button>'
        }
        modalFooter.innerHTML = buttons;
        console.log("chosen image: ", this.currentImage.currentSrc)
        this.prefetchAdjacentImages(this.currentImage);
    }
	connectedCallback () {
		console.log('connected!', this);
        const linkObserver = new MutationObserver((mutations, obs) => {
            for (let mutation of mutations) {
                if (mutation.type === 'childList') {
                    let thumbnailLinks = this.querySelectorAll('.cast-gallery-container > a');
                    thumbnailLinks.forEach((link) => {
                        if (!link.classList.contains('event-added')) {
                            link.addEventListener('click', (event) => {
                                event.preventDefault();
                                // console.log('clicked', event.target);
                                this.setModalImage(event.target);
                            });
                            link.classList.add('event-added');
                        }
                    });
                    obs.disconnect(); // Disconnect after initial setup
                }
            }
        });
        linkObserver.observe(this, { childList: true, subtree: true });

        const footerObserver = new MutationObserver((mutations, obs) => {
            const modalFooter = this.querySelector(".modal-footer");
            if (modalFooter) {
                modalFooter.addEventListener("click", (event) => {
                    if (event.target.matches("#data-prev, #data-next")) {
                        this.replaceImage(event.target.id);
                    }
                });
                obs.disconnect(); // Disconnect once the modalFooter is found and event listener is added
            }
        });
        footerObserver.observe(this, { childList: true, subtree: true });

        this.addEventListener('keydown', function (e) {
            if (e.keyCode === 37) {
                this.replaceImage('data-prev')
            }
            if (e.keyCode === 39) {
                this.replaceImage('data-next')
            }
        });
	}
	disconnectedCallback () {
		console.log('disconnected', this);
	}
}

// Define the new web component
ImageGallery.register();
