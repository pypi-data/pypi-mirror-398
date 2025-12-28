"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["3777"],{56750:function(e,t,i){i.d(t,{a:function(){return l}});i(74423);var a=i(31136),n=i(41144);function l(e,t){var i=(0,n.m)(e.entity_id),l=void 0!==t?t:null==e?void 0:e.state;if(["button","event","input_button","scene"].includes(i))return l!==a.Hh;if((0,a.g0)(l))return!1;if(l===a.KF&&"alert"!==i)return!1;switch(i){case"alarm_control_panel":return"disarmed"!==l;case"alert":return"idle"!==l;case"cover":case"valve":return"closed"!==l;case"device_tracker":case"person":return"not_home"!==l;case"lawn_mower":return["mowing","error"].includes(l);case"lock":return"locked"!==l;case"media_player":return"standby"!==l;case"vacuum":return!["idle","docked","paused"].includes(l);case"plant":return"problem"===l;case"group":return["on","home","open","locked","problem"].includes(l);case"timer":return"active"===l;case"camera":return"streaming"===l}return!0}},17509:function(e,t,i){i.a(e,(async function(e,a){try{i.r(t),i.d(t,{HaMediaSelector:function(){return Z}});var n=i(44734),l=i(56038),o=i(69683),s=i(6454),d=(i(28706),i(74423),i(62062),i(18111),i(61701),i(26099),i(62826)),c=i(96196),r=i(77845),u=i(94333),h=i(92542),v=i(9477),m=i(54193),_=i(92001),p=i(76681),b=(i(17963),i(91120),i(1214)),y=i(55376),g=i(41881),f=e([g]);g=(f.then?(await f)():f)[0];var k,$,x,w,M,H,E,q,A,C,z,I,O=e=>e,j=[{name:"media_content_id",required:!1,selector:{text:{}}},{name:"media_content_type",required:!1,selector:{text:{}}}],V=["media_player"],U={},Z=function(e){function t(){var e;(0,n.A)(this,t);for(var i=arguments.length,a=new Array(i),l=0;l<i;l++)a[l]=arguments[l];return(e=(0,o.A)(this,t,[].concat(a))).disabled=!1,e.required=!0,e._computeLabelCallback=t=>e.hass.localize(`ui.components.selectors.media.${t.name}`),e._computeHelperCallback=t=>e.hass.localize(`ui.components.selectors.media.${t.name}_detail`),e}return(0,s.A)(t,e),(0,l.A)(t,[{key:"_hasAccept",get:function(){var e;return!(null===(e=this.selector)||void 0===e||null===(e=e.media)||void 0===e||null===(e=e.accept)||void 0===e||!e.length)}},{key:"willUpdate",value:function(e){var t;e.has("context")&&(this._hasAccept||(this._contextEntities=(0,y.e)(null===(t=this.context)||void 0===t?void 0:t.filter_entity)));if(e.has("value")){var i,a,n=null===(i=this.value)||void 0===i||null===(i=i.metadata)||void 0===i?void 0:i.thumbnail;if(n===(null===(a=e.get("value"))||void 0===a||null===(a=a.metadata)||void 0===a?void 0:a.thumbnail))return;if(n&&n.startsWith("/"))this._thumbnailUrl=void 0,(0,m.e0)(this.hass,n).then((e=>{this._thumbnailUrl=e.path}));else if(n&&n.startsWith("https://brands.home-assistant.io")){var l;this._thumbnailUrl=(0,p.MR)({domain:(0,p.a_)(n),type:"icon",useFallback:!0,darkOptimized:null===(l=this.hass.themes)||void 0===l?void 0:l.darkMode})}else this._thumbnailUrl=n}}},{key:"render",value:function(){var e,t,i,a,n,l,o,s,d,r,h=this._getActiveEntityId(),m=h?this.hass.states[h]:void 0,p=!h||m&&(0,v.$)(m,_.vj.BROWSE_MEDIA);return null!==(e=this.selector.media)&&void 0!==e&&e.image_upload&&!this.value?(0,c.qy)(k||(k=O`${0}
        <ha-picture-upload
          .hass=${0}
          .value=${0}
          .contentIdHelper=${0}
          select-media
          full-media
          @media-picked=${0}
        ></ha-picture-upload>`),this.label?(0,c.qy)($||($=O`<label>${0}</label>`),this.label):c.s6,this.hass,null,null===(r=this.selector.media)||void 0===r?void 0:r.content_id_helper,this._pictureUploadMediaPicked):(0,c.qy)(x||(x=O`
      ${0}
      ${0}
    `),this._hasAccept||this._contextEntities&&this._contextEntities.length<=1?c.s6:(0,c.qy)(w||(w=O`
            <ha-entity-picker
              .hass=${0}
              .value=${0}
              .label=${0}
              .disabled=${0}
              .helper=${0}
              .required=${0}
              .hideClearIcon=${0}
              .includeDomains=${0}
              .includeEntities=${0}
              .allowCustomEntity=${0}
              @value-changed=${0}
            ></ha-entity-picker>
          `),this.hass,h,this.label||this.hass.localize("ui.components.selectors.media.pick_media_player"),this.disabled,this.helper,this.required,!!this._contextEntities,V,this._contextEntities,!this._contextEntities,this._entityChanged),p?(0,c.qy)(E||(E=O`${0}
            <ha-card
              outlined
              tabindex="0"
              role="button"
              aria-label=${0}
              @click=${0}
              @keydown=${0}
              class=${0}
            >
              <div class="content-container">
                <div class="thumbnail">
                  ${0}
                </div>
                <div class="title">
                  ${0}
                </div>
              </div>
            </ha-card>
            ${0}`),this.label?(0,c.qy)(q||(q=O`<label>${0}</label>`),this.label):c.s6,null!==(t=this.value)&&void 0!==t&&t.media_content_id?(null===(i=this.value.metadata)||void 0===i?void 0:i.title)||this.value.media_content_id:this.hass.localize("ui.components.selectors.media.pick_media"),this._pickMedia,this._handleKeyDown,this.disabled||!h&&!this._hasAccept?"disabled":"",null!==(a=this.value)&&void 0!==a&&null!==(a=a.metadata)&&void 0!==a&&a.thumbnail?(0,c.qy)(A||(A=O`
                        <div
                          class="${0}
                          image"
                          style=${0}
                        ></div>
                      `),(0,u.H)({"centered-image":!!this.value.metadata.media_class&&["app","directory"].includes(this.value.metadata.media_class)}),this._thumbnailUrl?`background-image: url(${this._thumbnailUrl});`:""):(0,c.qy)(C||(C=O`
                        <div class="icon-holder image">
                          <ha-svg-icon
                            class="folder"
                            .path=${0}
                          ></ha-svg-icon>
                        </div>
                      `),null!==(n=this.value)&&void 0!==n&&n.media_content_id?null!==(l=this.value)&&void 0!==l&&null!==(l=l.metadata)&&void 0!==l&&l.media_class?_.EC["directory"===this.value.metadata.media_class&&this.value.metadata.children_media_class||this.value.metadata.media_class].icon:"M19 3H5C3.89 3 3 3.89 3 5V19C3 20.1 3.9 21 5 21H19C20.1 21 21 20.1 21 19V5C21 3.89 20.1 3 19 3M10 16V8L15 12":"M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"),null!==(o=this.value)&&void 0!==o&&o.media_content_id?(null===(s=this.value.metadata)||void 0===s?void 0:s.title)||this.value.media_content_id:this.hass.localize("ui.components.selectors.media.pick_media"),null!==(d=this.selector.media)&&void 0!==d&&d.clearable?(0,c.qy)(z||(z=O`<div>
                  <ha-button
                    appearance="plain"
                    size="small"
                    variant="danger"
                    @click=${0}
                  >
                    ${0}
                  </ha-button>
                </div>`),this._clearValue,this.hass.localize("ui.components.picture-upload.clear_picture")):c.s6):(0,c.qy)(M||(M=O`
            ${0}
            <ha-alert>
              ${0}
            </ha-alert>
            <ha-form
              .hass=${0}
              .data=${0}
              .schema=${0}
              .computeLabel=${0}
              .computeHelper=${0}
            ></ha-form>
          `),this.label?(0,c.qy)(H||(H=O`<label>${0}</label>`),this.label):c.s6,this.hass.localize("ui.components.selectors.media.browse_not_supported"),this.hass,this.value||U,j,this._computeLabelCallback,this._computeHelperCallback))}},{key:"_entityChanged",value:function(e){var t;e.stopPropagation(),!this._hasAccept&&null!==(t=this.context)&&void 0!==t&&t.filter_entity?(0,h.r)(this,"value-changed",{value:{media_content_id:"",media_content_type:"",metadata:{browse_entity_id:e.detail.value}}}):(0,h.r)(this,"value-changed",{value:{entity_id:e.detail.value,media_content_id:"",media_content_type:""}})}},{key:"_pickMedia",value:function(){var e,t,i,a,n,l;(0,b.O)(this,{action:"pick",entityId:this._getActiveEntityId(),navigateIds:null===(e=this.value)||void 0===e||null===(e=e.metadata)||void 0===e?void 0:e.navigateIds,accept:null===(t=this.selector.media)||void 0===t?void 0:t.accept,defaultId:null===(i=this.value)||void 0===i?void 0:i.media_content_id,defaultType:null===(a=this.value)||void 0===a?void 0:a.media_content_type,hideContentType:null===(n=this.selector.media)||void 0===n?void 0:n.hide_content_type,contentIdHelper:null===(l=this.selector.media)||void 0===l?void 0:l.content_id_helper,mediaPickedCallback:e=>{var t,i;(0,h.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.value),{},{media_content_id:e.item.media_content_id,media_content_type:e.item.media_content_type,metadata:Object.assign({title:e.item.title,thumbnail:e.item.thumbnail,media_class:e.item.media_class,children_media_class:e.item.children_media_class,navigateIds:null===(t=e.navigateIds)||void 0===t?void 0:t.map((e=>({media_content_type:e.media_content_type,media_content_id:e.media_content_id})))},!this._hasAccept&&null!==(i=this.context)&&void 0!==i&&i.filter_entity?{browse_entity_id:this._getActiveEntityId()}:{})})})}})}},{key:"_getActiveEntityId",value:function(){var e,t,i,a,n=null===(e=this.value)||void 0===e||null===(e=e.metadata)||void 0===e?void 0:e.browse_entity_id;return(null===(t=this.value)||void 0===t?void 0:t.entity_id)||n&&(null===(i=this._contextEntities)||void 0===i?void 0:i.includes(n))&&n||(null===(a=this._contextEntities)||void 0===a?void 0:a[0])}},{key:"_handleKeyDown",value:function(e){"Enter"!==e.key&&" "!==e.key||(e.preventDefault(),this._pickMedia())}},{key:"_pictureUploadMediaPicked",value:function(e){var t,i=e.detail;(0,h.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.value),{},{media_content_id:i.item.media_content_id,media_content_type:i.item.media_content_type,metadata:{title:i.item.title,thumbnail:i.item.thumbnail,media_class:i.item.media_class,children_media_class:i.item.children_media_class,navigateIds:null===(t=i.navigateIds)||void 0===t?void 0:t.map((e=>({media_content_type:e.media_content_type,media_content_id:e.media_content_id})))}})})}},{key:"_clearValue",value:function(){(0,h.r)(this,"value-changed",{value:void 0})}}])}(c.WF);Z.styles=(0,c.AH)(I||(I=O`
    ha-entity-picker {
      display: block;
      margin-bottom: 16px;
    }
    ha-alert {
      display: block;
      margin-bottom: 16px;
    }
    ha-card {
      position: relative;
      width: 100%;
      box-sizing: border-box;
      cursor: pointer;
      transition: background-color 180ms ease-in-out;
      min-height: 56px;
    }
    ha-card:hover:not(.disabled),
    ha-card:focus:not(.disabled) {
      background-color: var(--state-icon-hover-color, rgba(0, 0, 0, 0.04));
    }
    ha-card:focus {
      outline: none;
    }
    ha-card.disabled {
      pointer-events: none;
      color: var(--disabled-text-color);
    }
    .content-container {
      display: flex;
      align-items: center;
      padding: 8px;
      gap: var(--ha-space-3);
    }
    ha-card .thumbnail {
      width: 40px;
      height: 40px;
      flex-shrink: 0;
      position: relative;
      box-sizing: border-box;
      border-radius: var(--ha-border-radius-md);
      overflow: hidden;
    }
    ha-card .image {
      border-radius: var(--ha-border-radius-md);
    }
    .folder {
      --mdc-icon-size: 24px;
    }
    .title {
      font-size: var(--ha-font-size-m);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      line-height: 1.4;
      flex: 1;
      min-width: 0;
    }
    .image {
      position: absolute;
      top: 0;
      right: 0;
      left: 0;
      bottom: 0;
      background-size: cover;
      background-repeat: no-repeat;
      background-position: center;
    }
    .centered-image {
      margin: 4px;
      background-size: contain;
    }
    .icon-holder {
      display: flex;
      justify-content: center;
      align-items: center;
      width: 100%;
      height: 100%;
    }
  `)),(0,d.__decorate)([(0,r.MZ)({attribute:!1})],Z.prototype,"hass",void 0),(0,d.__decorate)([(0,r.MZ)({attribute:!1})],Z.prototype,"selector",void 0),(0,d.__decorate)([(0,r.MZ)({attribute:!1})],Z.prototype,"value",void 0),(0,d.__decorate)([(0,r.MZ)()],Z.prototype,"label",void 0),(0,d.__decorate)([(0,r.MZ)()],Z.prototype,"helper",void 0),(0,d.__decorate)([(0,r.MZ)({type:Boolean,reflect:!0})],Z.prototype,"disabled",void 0),(0,d.__decorate)([(0,r.MZ)({type:Boolean,reflect:!0})],Z.prototype,"required",void 0),(0,d.__decorate)([(0,r.MZ)({attribute:!1})],Z.prototype,"context",void 0),(0,d.__decorate)([(0,r.wk)()],Z.prototype,"_thumbnailUrl",void 0),Z=(0,d.__decorate)([(0,r.EM)("ha-selector-media")],Z),a()}catch(D){a(D)}}))},54193:function(e,t,i){i.d(t,{Hg:function(){return a},e0:function(){return n}});i(61397),i(50264),i(74423),i(62062),i(18111),i(61701),i(33110),i(26099),i(3362);var a=e=>e.map((e=>{if("string"!==e.type)return e;switch(e.name){case"username":return Object.assign(Object.assign({},e),{},{autocomplete:"username",autofocus:!0});case"password":return Object.assign(Object.assign({},e),{},{autocomplete:"current-password"});case"code":return Object.assign(Object.assign({},e),{},{autocomplete:"one-time-code",autofocus:!0});default:return e}})),n=(e,t)=>e.callWS({type:"auth/sign_path",path:t})},31136:function(e,t,i){i.d(t,{HV:function(){return l},Hh:function(){return n},KF:function(){return s},ON:function(){return o},g0:function(){return r},s7:function(){return d}});var a=i(99245),n="unavailable",l="unknown",o="on",s="off",d=[n,l],c=[n,l,s],r=(0,a.g)(d);(0,a.g)(c)}}]);
//# sourceMappingURL=3777.376edd56b6010c2d.js.map