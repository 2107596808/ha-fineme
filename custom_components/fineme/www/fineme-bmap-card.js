class FinemeBMapCard extends HTMLElement {
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
    this._zoom = config.zoom || 18;
    this._height = config.height || 400;
    this._bmapKey = config.bmap_key || '';
    this._style = config.map_style || 'normal';
  }

  getCardSize() {
    return Math.ceil(this._height / 50);
  }

  _init() {
    this._initialized = true;
    this.style.display = 'block';
    this.style.height = this._height + 'px';
    this.style.position = 'relative';

    this._container = document.createElement('div');
    this._container.style.cssText = 'width:100%;height:100%;border-radius:var(--ha-card-border-radius,12px);overflow:hidden;';
    this.appendChild(this._container);
    this._loadBMap();
  }

  _loadBMap() {
    if (window.BMapGL) {
      this._createMap();
      return;
    }
    if (document.getElementById('bmap-js-api')) {
      const checkInterval = setInterval(() => {
        if (window.BMapGL) {
          clearInterval(checkInterval);
          this._createMap();
        }
      }, 200);
      return;
    }
    const script = document.createElement('script');
    script.id = 'bmap-js-api';
    script.src = `https://api.map.baidu.com/api?v=3.0&type=webgl&ak=${this._bmapKey}`;
    script.onload = () => this._createMap();
    document.head.appendChild(script);
  }

  _createMap() {
    if (!window.BMapGL) return;
    if (!this._container) return;

    const BMapGL = window.BMapGL;
    this._map = new BMapGL.Map(this._container);
    this._map.centerAndZoom(new BMapGL.Point(116.404, 39.915), this._zoom);
    this._map.enableScrollWheelZoom(true);

    if (this._style && this._style !== 'normal') {
      this._map.setMapStyleV2({ styleId: this._style });
    }

    this._marker = new BMapGL.Marker(new BMapGL.Point(116.404, 39.915));
    this._map.addOverlay(this._marker);

    // Info window
    this._infoWindow = new BMapGL.InfoWindow('', { width: 220, offset: new BMapGL.Size(0, -10) });

    this._update();
  }

  _update() {
    if (!this._hass || !this._map || !this._marker) return;
    const entity = this._hass.states[this._entityId];
    if (!entity) return;

    const attrs = entity.attributes || {};
    // Baidu map uses BD09 coordinates directly from attributes
    let lat = parseFloat(attrs.bd09_latitude);
    let lng = parseFloat(attrs.bd09_longitude);

    if (!lat || !lng || isNaN(lat) || isNaN(lng)) {
      lat = parseFloat(entity.attributes.latitude);
      lng = parseFloat(entity.attributes.longitude);
    }
    if (!lat || !lng) return;

    const BMapGL = window.BMapGL;
    const point = new BMapGL.Point(lng, lat);
    this._marker.setPosition(point);
    this._map.panTo(point);

    const speed = attrs.speed !== undefined ? `${attrs.speed} km/h` : '';
    const posTime = attrs.position_time || '';
    const source = attrs.location_source || '';
    const battery = this._config.battery_entity
      ? (this._hass.states[this._config.battery_entity]?.state || '?')
      : '';

    let content = `<div style="font-size:13px;line-height:1.8;">
      <b>${entity.attributes.friendly_name || this._entityId}</b><br>`;
    if (posTime) content += `📍 ${posTime}<br>`;
    if (speed) content += `🏃 ${speed}<br>`;
    if (source) content += `📡 ${source}<br>`;
    if (battery) content += `🔋 ${battery}%<br>`;
    content += `🌐 ${lat.toFixed(6)}, ${lng.toFixed(6)}</div>`;

    this._infoWindow.setContent(content);
    this._marker.openInfoWindow(this._infoWindow);
  }

  static getStubConfig() {
    return {
      entity: 'device_tracker.fineme_tracker',
      zoom: 18,
      height: 400,
      bmap_key: '',
      map_style: 'normal',
    };
  }
}

customElements.define('fineme-bmap-card', FinemeBMapCard);
