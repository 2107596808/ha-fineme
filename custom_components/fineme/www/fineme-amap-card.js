class FinemeAMapCard extends HTMLElement {
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
    this._amapKey = config.amap_key || '';
    this._style = config.map_style || 'amap://styles/normal';
    this._useBD09 = config.use_bd09 || false;
  }

  getCardSize() {
    return Math.ceil(this._height / 50);
  }

  _init() {
    this._initialized = true;
    this.style.display = 'block';
    this.style.height = this._height + 'px';
    this.style.position = 'relative';
    this.innerHTML = `<div id="amap-container-${this._entityId.replace('.', '-')}"
      style="width:100%;height:100%;border-radius:var(--ha-card-border-radius,12px);overflow:hidden;"></div>`;
    this._loadAMap();
  }

  _loadAMap() {
    if (window.AMap) {
      this._createMap();
      return;
    }
    if (document.getElementById('amap-js-api')) {
      const checkInterval = setInterval(() => {
        if (window.AMap) {
          clearInterval(checkInterval);
          this._createMap();
        }
      }, 200);
      return;
    }
    const script = document.createElement('script');
    script.id = 'amap-js-api';
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${this._amapKey}`;
    script.onload = () => this._createMap();
    document.head.appendChild(script);
  }

  _createMap() {
    if (!window.AMap) return;
    const containerId = `amap-container-${this._entityId.replace('.', '-')}`;
    const container = this.querySelector(`#${containerId}`);
    if (!container) return;

    this._map = new AMap.Map(container, {
      zoom: this._zoom,
      center: [116.397428, 39.90923],
      mapStyle: this._style,
      viewMode: '2D',
    });

    this._marker = new AMap.Marker({
      map: this._map,
      animation: 'AMAP_ANIMATION_DROP',
    });

    this._circle = new AMap.Circle({
      map: this._map,
      strokeColor: '#3388ff',
      strokeWeight: 2,
      strokeOpacity: 0.5,
      fillColor: '#3388ff',
      fillOpacity: 0.1,
    });

    this._update();
  }

  _update() {
    if (!this._hass || !this._map || !this._marker) return;
    const entity = this._hass.states[this._entityId];
    if (!entity) return;

    let lat, lng;
    const attrs = entity.attributes || {};

    if (this._useBD09 && attrs.bd09_latitude && attrs.bd09_longitude) {
      lat = parseFloat(attrs.bd09_latitude);
      lng = parseFloat(attrs.bd09_longitude);
    } else {
      lat = parseFloat(entity.attributes.latitude);
      lng = parseFloat(entity.attributes.longitude);
    }

    if (!lat || !lng || isNaN(lat) || isNaN(lng)) return;

    const position = new AMap.LngLat(lng, lat);
    this._marker.setPosition(position);
    this._map.setCenter(position);

    const accuracy = parseFloat(attrs.gps_accuracy) || 0;
    if (accuracy > 0) {
      this._circle.setCenter(position);
      this._circle.setRadius(accuracy);
      this._circle.show();
    } else {
      this._circle.hide();
    }

    const speed = attrs.speed !== undefined ? `${attrs.speed} km/h` : '';
    const posTime = attrs.position_time || '';
    const source = attrs.location_source || '';
    const battery = this._config.battery_entity
      ? (this._hass.states[this._config.battery_entity]?.state || '?')
      : '';

    let infoContent = `<div style="font-size:13px;line-height:1.8;padding:4px 8px;">
      <b>${entity.attributes.friendly_name || this._entityId}</b><br>`;
    if (posTime) infoContent += `📍 ${posTime}<br>`;
    if (speed) infoContent += `🏃 ${speed}<br>`;
    if (source) infoContent += `📡 ${source}<br>`;
    if (battery) infoContent += `🔋 ${battery}%<br>`;
    infoContent += `🌐 ${lat.toFixed(6)}, ${lng.toFixed(6)}`;
    infoContent += '</div>';

    if (!this._infoWindow) {
      this._infoWindow = new AMap.InfoWindow({ offset: new AMap.Pixel(0, -30) });
    }
    this._infoWindow.setContent(infoContent);
    this._infoWindow.open(this._map, position);
  }

  static getStubConfig() {
    return {
      entity: 'device_tracker.fineme_tracker',
      zoom: 16,
      height: 400,
      amap_key: '',  // 请填写你的高德 JS API Key
      map_style: 'amap://styles/normal',
      use_bd09: false,
    };
  }
}

customElements.define('fineme-amap-card', FinemeAMapCard);
