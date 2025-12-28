"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["1656"],{66971:function(e,t,a){a.r(t),a.d(t,{HaBackupLocationSelector:function(){return B}});var r,o,s,i,n,u=a(44734),h=a(56038),l=a(69683),c=a(6454),p=(a(28706),a(62826)),d=a(96196),_=a(77845),v=a(61397),A=a(50264),f=(a(2008),a(74423),a(62062),a(26910),a(18111),a(22489),a(61701),a(26099),a(22786)),m=a(92209),y=a(92542),k=a(55124),b=a(25749),M=function(e){return e.BIND="bind",e.CIFS="cifs",e.NFS="nfs",e}({}),g=function(e){return e.BACKUP="backup",e.MEDIA="media",e.SHARE="share",e}({}),$=function(){var e=(0,A.A)((0,v.A)().m((function e(t){return(0,v.A)().w((function(e){for(;;)if(0===e.n)return e.a(2,t.callWS({type:"supervisor/api",endpoint:"/mounts",method:"get",timeout:null}))}),e)})));return function(t){return e.apply(this,arguments)}}(),C=(a(17963),a(56565),a(69869),e=>e),Z="/backup",H=function(e){function t(){var e;(0,u.A)(this,t);for(var a=arguments.length,r=new Array(a),o=0;o<a;o++)r[o]=arguments[o];return(e=(0,l.A)(this,t,[].concat(r))).disabled=!1,e.required=!1,e._filterMounts=(0,f.A)(((t,a)=>{var r=t.mounts.filter((e=>[M.CIFS,M.NFS].includes(e.type)));return a&&(r=t.mounts.filter((e=>e.usage===a))),r.sort(((a,r)=>a.name===t.default_backup_mount?-1:r.name===t.default_backup_mount?1:(0,b.SH)(a.name,r.name,e.hass.locale.language)))})),e}return(0,c.A)(t,e),(0,h.A)(t,[{key:"firstUpdated",value:function(){this._getMounts()}},{key:"render",value:function(){if(this._error)return(0,d.qy)(r||(r=C`<ha-alert alert-type="error">${0}</ha-alert>`),this._error);if(!this._mounts)return d.s6;var e=(0,d.qy)(o||(o=C`<ha-list-item
      graphic="icon"
      .value=${0}
    >
      <span>
        ${0}
      </span>
      <ha-svg-icon slot="graphic" .path=${0}></ha-svg-icon>
    </ha-list-item>`),Z,this.hass.localize("ui.components.mount-picker.use_datadisk")||"Use data disk for backup","M6,2H18A2,2 0 0,1 20,4V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V4A2,2 0 0,1 6,2M12,4A6,6 0 0,0 6,10C6,13.31 8.69,16 12.1,16L11.22,13.77C10.95,13.29 11.11,12.68 11.59,12.4L12.45,11.9C12.93,11.63 13.54,11.79 13.82,12.27L15.74,14.69C17.12,13.59 18,11.9 18,10A6,6 0 0,0 12,4M12,9A1,1 0 0,1 13,10A1,1 0 0,1 12,11A1,1 0 0,1 11,10A1,1 0 0,1 12,9M7,18A1,1 0 0,0 6,19A1,1 0 0,0 7,20A1,1 0 0,0 8,19A1,1 0 0,0 7,18M12.09,13.27L14.58,19.58L17.17,18.08L12.95,12.77L12.09,13.27Z");return(0,d.qy)(s||(s=C`
      <ha-select
        .label=${0}
        .value=${0}
        .required=${0}
        .disabled=${0}
        .helper=${0}
        @selected=${0}
        @closed=${0}
        fixedMenuPosition
        naturalMenuWidth
      >
        ${0}
        ${0}
        ${0}
      </ha-select>
    `),void 0===this.label&&this.hass?this.hass.localize("ui.components.mount-picker.mount"):this.label,this._value,this.required,this.disabled,this.helper,this._mountChanged,k.d,this.usage!==g.BACKUP||this._mounts.default_backup_mount&&this._mounts.default_backup_mount!==Z?d.s6:e,this._filterMounts(this._mounts,this.usage).map((e=>(0,d.qy)(i||(i=C`<ha-list-item twoline graphic="icon" .value=${0}>
              <span>${0}</span>
              <span slot="secondary"
                >${0}${0}${0}</span
              >
              <ha-svg-icon
                slot="graphic"
                .path=${0}
              ></ha-svg-icon>
            </ha-list-item>`),e.name,e.name,e.server,e.port?`:${e.port}`:d.s6,e.type===M.NFS?e.path:`:${e.share}`,e.usage===g.MEDIA?"M19 3H5C3.89 3 3 3.89 3 5V19C3 20.1 3.9 21 5 21H19C20.1 21 21 20.1 21 19V5C21 3.89 20.1 3 19 3M10 16V8L15 12":e.usage===g.SHARE?"M10,4H4C2.89,4 2,4.89 2,6V18A2,2 0 0,0 4,20H20A2,2 0 0,0 22,18V8C22,6.89 21.1,6 20,6H12L10,4Z":"M12,3A9,9 0 0,0 3,12H0L4,16L8,12H5A7,7 0 0,1 12,5A7,7 0 0,1 19,12A7,7 0 0,1 12,19C10.5,19 9.09,18.5 7.94,17.7L6.5,19.14C8.04,20.3 9.94,21 12,21A9,9 0 0,0 21,12A9,9 0 0,0 12,3M14,12A2,2 0 0,0 12,10A2,2 0 0,0 10,12A2,2 0 0,0 12,14A2,2 0 0,0 14,12Z"))),this.usage===g.BACKUP&&this._mounts.default_backup_mount?e:d.s6)}},{key:"_getMounts",value:(a=(0,A.A)((0,v.A)().m((function e(){return(0,v.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:if(e.p=0,!(0,m.x)(this.hass,"hassio")){e.n=2;break}return e.n=1,$(this.hass);case 1:this._mounts=e.v,this.usage!==g.BACKUP||this.value||(this.value=this._mounts.default_backup_mount||Z),e.n=3;break;case 2:this._error=this.hass.localize("ui.components.mount-picker.error.no_supervisor");case 3:e.n=5;break;case 4:e.p=4,e.v,this._error=this.hass.localize("ui.components.mount-picker.error.fetch_mounts");case 5:return e.a(2)}}),e,this,[[0,4]])}))),function(){return a.apply(this,arguments)})},{key:"_value",get:function(){return this.value||""}},{key:"_mountChanged",value:function(e){e.stopPropagation();var t=e.target.value;t!==this._value&&this._setValue(t)}},{key:"_setValue",value:function(e){this.value=e,setTimeout((()=>{(0,y.r)(this,"value-changed",{value:e}),(0,y.r)(this,"change")}),0)}}],[{key:"styles",get:function(){return[(0,d.AH)(n||(n=C`
        ha-select {
          width: 100%;
        }
      `))]}}]);var a}(d.WF);(0,p.__decorate)([(0,_.MZ)()],H.prototype,"label",void 0),(0,p.__decorate)([(0,_.MZ)()],H.prototype,"value",void 0),(0,p.__decorate)([(0,_.MZ)()],H.prototype,"helper",void 0),(0,p.__decorate)([(0,_.MZ)({type:Boolean})],H.prototype,"disabled",void 0),(0,p.__decorate)([(0,_.MZ)({type:Boolean})],H.prototype,"required",void 0),(0,p.__decorate)([(0,_.MZ)()],H.prototype,"usage",void 0),(0,p.__decorate)([(0,_.wk)()],H.prototype,"_mounts",void 0),(0,p.__decorate)([(0,_.wk)()],H.prototype,"_error",void 0),H=(0,p.__decorate)([(0,_.EM)("ha-mount-picker")],H);var q,L,w=e=>e,B=function(e){function t(){var e;(0,u.A)(this,t);for(var a=arguments.length,r=new Array(a),o=0;o<a;o++)r[o]=arguments[o];return(e=(0,l.A)(this,t,[].concat(r))).disabled=!1,e.required=!0,e}return(0,c.A)(t,e),(0,h.A)(t,[{key:"render",value:function(){return(0,d.qy)(q||(q=w`<ha-mount-picker
      .hass=${0}
      .value=${0}
      .label=${0}
      .helper=${0}
      .disabled=${0}
      .required=${0}
      usage="backup"
    ></ha-mount-picker>`),this.hass,this.value,this.label,this.helper,this.disabled,this.required)}}])}(d.WF);B.styles=(0,d.AH)(L||(L=w`
    ha-mount-picker {
      width: 100%;
    }
  `)),(0,p.__decorate)([(0,_.MZ)({attribute:!1})],B.prototype,"hass",void 0),(0,p.__decorate)([(0,_.MZ)({attribute:!1})],B.prototype,"selector",void 0),(0,p.__decorate)([(0,_.MZ)()],B.prototype,"value",void 0),(0,p.__decorate)([(0,_.MZ)()],B.prototype,"label",void 0),(0,p.__decorate)([(0,_.MZ)()],B.prototype,"helper",void 0),(0,p.__decorate)([(0,_.MZ)({type:Boolean})],B.prototype,"disabled",void 0),(0,p.__decorate)([(0,_.MZ)({type:Boolean})],B.prototype,"required",void 0),B=(0,p.__decorate)([(0,_.EM)("ha-selector-backup_location")],B)}}]);
//# sourceMappingURL=1656.a400d82f076dd491.js.map