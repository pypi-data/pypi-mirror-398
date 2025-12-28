export const __webpack_id__="1656";export const __webpack_ids__=["1656"];export const __webpack_modules__={66971:function(e,t,s){s.r(t),s.d(t,{HaBackupLocationSelector:()=>m});var a=s(62826),o=s(96196),i=s(77845),r=s(22786),u=s(92209),n=s(92542),h=s(55124),l=s(25749),p=function(e){return e.BIND="bind",e.CIFS="cifs",e.NFS="nfs",e}({}),c=function(e){return e.BACKUP="backup",e.MEDIA="media",e.SHARE="share",e}({});s(17963),s(56565),s(69869);const d="/backup";class _ extends o.WF{firstUpdated(){this._getMounts()}render(){if(this._error)return o.qy`<ha-alert alert-type="error">${this._error}</ha-alert>`;if(!this._mounts)return o.s6;const e=o.qy`<ha-list-item
      graphic="icon"
      .value=${d}
    >
      <span>
        ${this.hass.localize("ui.components.mount-picker.use_datadisk")||"Use data disk for backup"}
      </span>
      <ha-svg-icon slot="graphic" .path=${"M6,2H18A2,2 0 0,1 20,4V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V4A2,2 0 0,1 6,2M12,4A6,6 0 0,0 6,10C6,13.31 8.69,16 12.1,16L11.22,13.77C10.95,13.29 11.11,12.68 11.59,12.4L12.45,11.9C12.93,11.63 13.54,11.79 13.82,12.27L15.74,14.69C17.12,13.59 18,11.9 18,10A6,6 0 0,0 12,4M12,9A1,1 0 0,1 13,10A1,1 0 0,1 12,11A1,1 0 0,1 11,10A1,1 0 0,1 12,9M7,18A1,1 0 0,0 6,19A1,1 0 0,0 7,20A1,1 0 0,0 8,19A1,1 0 0,0 7,18M12.09,13.27L14.58,19.58L17.17,18.08L12.95,12.77L12.09,13.27Z"}></ha-svg-icon>
    </ha-list-item>`;return o.qy`
      <ha-select
        .label=${void 0===this.label&&this.hass?this.hass.localize("ui.components.mount-picker.mount"):this.label}
        .value=${this._value}
        .required=${this.required}
        .disabled=${this.disabled}
        .helper=${this.helper}
        @selected=${this._mountChanged}
        @closed=${h.d}
        fixedMenuPosition
        naturalMenuWidth
      >
        ${this.usage!==c.BACKUP||this._mounts.default_backup_mount&&this._mounts.default_backup_mount!==d?o.s6:e}
        ${this._filterMounts(this._mounts,this.usage).map((e=>o.qy`<ha-list-item twoline graphic="icon" .value=${e.name}>
              <span>${e.name}</span>
              <span slot="secondary"
                >${e.server}${e.port?`:${e.port}`:o.s6}${e.type===p.NFS?e.path:`:${e.share}`}</span
              >
              <ha-svg-icon
                slot="graphic"
                .path=${e.usage===c.MEDIA?"M19 3H5C3.89 3 3 3.89 3 5V19C3 20.1 3.9 21 5 21H19C20.1 21 21 20.1 21 19V5C21 3.89 20.1 3 19 3M10 16V8L15 12":e.usage===c.SHARE?"M10,4H4C2.89,4 2,4.89 2,6V18A2,2 0 0,0 4,20H20A2,2 0 0,0 22,18V8C22,6.89 21.1,6 20,6H12L10,4Z":"M12,3A9,9 0 0,0 3,12H0L4,16L8,12H5A7,7 0 0,1 12,5A7,7 0 0,1 19,12A7,7 0 0,1 12,19C10.5,19 9.09,18.5 7.94,17.7L6.5,19.14C8.04,20.3 9.94,21 12,21A9,9 0 0,0 21,12A9,9 0 0,0 12,3M14,12A2,2 0 0,0 12,10A2,2 0 0,0 10,12A2,2 0 0,0 12,14A2,2 0 0,0 14,12Z"}
              ></ha-svg-icon>
            </ha-list-item>`))}
        ${this.usage===c.BACKUP&&this._mounts.default_backup_mount?e:o.s6}
      </ha-select>
    `}async _getMounts(){try{(0,u.x)(this.hass,"hassio")?(this._mounts=await(async e=>e.callWS({type:"supervisor/api",endpoint:"/mounts",method:"get",timeout:null}))(this.hass),this.usage!==c.BACKUP||this.value||(this.value=this._mounts.default_backup_mount||d)):this._error=this.hass.localize("ui.components.mount-picker.error.no_supervisor")}catch(e){this._error=this.hass.localize("ui.components.mount-picker.error.fetch_mounts")}}get _value(){return this.value||""}_mountChanged(e){e.stopPropagation();const t=e.target.value;t!==this._value&&this._setValue(t)}_setValue(e){this.value=e,setTimeout((()=>{(0,n.r)(this,"value-changed",{value:e}),(0,n.r)(this,"change")}),0)}static get styles(){return[o.AH`
        ha-select {
          width: 100%;
        }
      `]}constructor(...e){super(...e),this.disabled=!1,this.required=!1,this._filterMounts=(0,r.A)(((e,t)=>{let s=e.mounts.filter((e=>[p.CIFS,p.NFS].includes(e.type)));return t&&(s=e.mounts.filter((e=>e.usage===t))),s.sort(((t,s)=>t.name===e.default_backup_mount?-1:s.name===e.default_backup_mount?1:(0,l.SH)(t.name,s.name,this.hass.locale.language)))}))}}(0,a.__decorate)([(0,i.MZ)()],_.prototype,"label",void 0),(0,a.__decorate)([(0,i.MZ)()],_.prototype,"value",void 0),(0,a.__decorate)([(0,i.MZ)()],_.prototype,"helper",void 0),(0,a.__decorate)([(0,i.MZ)({type:Boolean})],_.prototype,"disabled",void 0),(0,a.__decorate)([(0,i.MZ)({type:Boolean})],_.prototype,"required",void 0),(0,a.__decorate)([(0,i.MZ)()],_.prototype,"usage",void 0),(0,a.__decorate)([(0,i.wk)()],_.prototype,"_mounts",void 0),(0,a.__decorate)([(0,i.wk)()],_.prototype,"_error",void 0),_=(0,a.__decorate)([(0,i.EM)("ha-mount-picker")],_);class m extends o.WF{render(){return o.qy`<ha-mount-picker
      .hass=${this.hass}
      .value=${this.value}
      .label=${this.label}
      .helper=${this.helper}
      .disabled=${this.disabled}
      .required=${this.required}
      usage="backup"
    ></ha-mount-picker>`}constructor(...e){super(...e),this.disabled=!1,this.required=!0}}m.styles=o.AH`
    ha-mount-picker {
      width: 100%;
    }
  `,(0,a.__decorate)([(0,i.MZ)({attribute:!1})],m.prototype,"hass",void 0),(0,a.__decorate)([(0,i.MZ)({attribute:!1})],m.prototype,"selector",void 0),(0,a.__decorate)([(0,i.MZ)()],m.prototype,"value",void 0),(0,a.__decorate)([(0,i.MZ)()],m.prototype,"label",void 0),(0,a.__decorate)([(0,i.MZ)()],m.prototype,"helper",void 0),(0,a.__decorate)([(0,i.MZ)({type:Boolean})],m.prototype,"disabled",void 0),(0,a.__decorate)([(0,i.MZ)({type:Boolean})],m.prototype,"required",void 0),m=(0,a.__decorate)([(0,i.EM)("ha-selector-backup_location")],m)}};
//# sourceMappingURL=1656.5a534834090af34e.js.map