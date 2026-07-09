class FinemeGMapCard extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    if (!this._initialized) {
      this._init();
    }
    this._update();
  }

  setConfig(config) {
    this._config = config;
    this._entityId = config.entity;
    this._zoom = config.zoom || 16;
    this._height = config.height || 400;
    this._gmapKey = config.gmap_key || '';
    this._mapType = config.map_type || 'roadmap';
  }

  getCardSize() {
    return Math.ceil(this._height / 50);
  }

  _init() {
    this._initialized = true;
    this.style.display = 'block';
    this.style.height = this._height + 'px';
    this.style.position = 'relative';
    this.innerHTML = `<div id="gmap-container-${this._entityId.replace('.', '-')}"
      style="width:100%;height:100%;border-radius:var(--ha-card-border-radius,12px);overflow:hidden;"></div>`;
    this._loadGMap();
  }

  _loadGMap() {
    if (window.google && window.google.maps) {
      this._createMap();
      return;
    }
    if (document.getElementById('gmap-js-api')) {
      const checkInterval = setInterval(() => {
        if (window.google && window.google.maps) {
          clearInterval(checkInterval);
          this._createMap();
        }
      }, 200);
      return;
    }
    const script = document.createElement('script');
    script.id = 'gmap-js-api';
    script.src = `https://maps.googleapis.com/maps/api/js?key=${this._gmapKey}&v=weekly`;
    script.onload = () => this._createMap();
    script.onerror = () => {
      this.innerHTML = `<div style="padding:20px;text-align:center;color:#f44;">
        Failed to load Google Maps API. Check your API key and network.</div>`;
    };
    document.head.appendChild(script);
  }

  _createMap() {
    if (!window.google || !window.google.maps) return;
    const containerId = `gmap-container-${this._entityId.replace('.', '-')}`;
    const container = this.querySelector(`#${containerId}`);
    if (!container) return;

    const gm = window.google.maps;
    this._map = new gm.Map(container, {
      zoom: this._zoom,
      center: { lat: 39.909, lng: 116.397 },
      mapTypeId: this._mapType,
      disableDefaultUI: false,
      zoomControl: true,
      streetViewControl: false,
      mapTypeControl: true,
    });

    this._marker = new gm.Marker({
      map: this._map,
      animation: gm.Animation.DROP,
    });

    this._circle = new gm.Circle({
      map: this._map,
      strokeColor: '#3388ff',
      strokeWeight: 2,
      strokeOpacity: 0.5,
      fillColor: '#3388ff',
      fillOpacity: 0.1,
    });

    this._infoWindow = new gm.InfoWindow();

    this._update();
  }

  _update() {
    if (!this._hass || !this._map || !this._marker) return;
    const entity = this._hass.states[this._entityId];
    if (!entity) return;

    const attrs = entity.attributes || {};
    // Google Maps uses WGS84 coordinates
    let lat = parseFloat(entity.attributes.latitude);
    let lng = parseFloat(entity.attributes.longitude);

    if (!lat || !lng || isNaN(lat) || isNaN(lng)) return;

    const gm = window.google.maps;
    const position = { lat, lng };
    this._marker.setPosition(position);
    this._map.panTo(position);

    const accuracy = parseFloat(attrs.gps_accuracy) || 0;
    if (accuracy > 0) {
      this._circle.setCenter(position);
      this._circle.setRadius(accuracy);
      this._circle.setVisible(true);
    } else {
      this._circle.setVisible(false);
    }

    const speed = attrs.speed !== undefined ? `${attrs.speed} km/h` : '';
    const posTime = attrs.position_time || '';
    const source = attrs.location_source || '';
    const battery = this._config.battery_entity
      ? (this._hass.states[this._config.battery_entity]?.state || '?')
      : '';

    let content = `<div style="font-size:13px;line-height:1.8;padding:4px 8px;">
      <b>${entity.attributes.friendly_name || this._entityId}</b><br>`;
    if (posTime) content += `📍 ${posTime}<br>`;
    if (speed) content += `🏃 ${speed}<br>`;
    if (source) content += `📡 ${source}<br>`;
    if (battery) content += `🔋 ${battery}%<br>`;
    content += `🌐 ${lat.toFixed(6)}, ${lng.toFixed(6)}</div>`;

    this._infoWindow.setContent(content);
    this._infoWindow.open(this._map, this._marker);
  }

  static getStubConfig() {
    return {
      entity: 'device_tracker.fineme_tracker',
      zoom: 16,
      height: 400,
      gmap_key: '',
      map_type: 'roadmap',
    };
  }
}

customElements.define('fineme-gmap-card', FinemeGMapCard);
