"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["8547"],{6062:function(a,e,i){i.a(a,(async function(a,n){try{i.r(e);var s=i(44734),t=i(56038),o=i(69683),l=i(6454),c=(i(28706),i(62826)),d=i(96196),r=i(77845),u=i(49284),h=i(92542),p=(i(17963),i(89473)),_=i(95637),g=(i(60733),i(39396)),f=i(91550),v=a([p,u]);[p,u]=v.then?(await v)():v;var y,b,m,$,A=a=>a,k=function(a){function e(){var a;(0,s.A)(this,e);for(var i=arguments.length,n=new Array(i),t=0;t<i;t++)n[t]=arguments[t];return(a=(0,o.A)(this,e,[].concat(n)))._obfuscateIp=!0,a}return(0,l.A)(e,a),(0,t.A)(e,[{key:"showDialog",value:function(a){this._params=a}},{key:"closeDialog",value:function(){var a,e;null===(a=this._params)||void 0===a||null===(e=a.closeDialog)||void 0===e||e.call(a),this._params=void 0,this._obfuscateIp=!0,(0,h.r)(this,"dialog-closed",{dialog:this.localName})}},{key:"render",value:function(){if(!this._params)return d.s6;var a=this._params.details;return(0,d.qy)(y||(y=A`
      <ha-dialog
        open
        @closed=${0}
        .heading=${0}
      >
        <div class="intro">
          <span>
            ${0}
          </span>
          <b>
            ${0}
          </b>
        </div>
        <div class="instance-details">
          ${0}
          ${0}
          <div class="instance-detail">
            <span>
              ${0}:
            </span>
            <div class="obfuscated">
              <span>
                ${0}
              </span>

              <ha-icon-button
                class="toggle-unmasked-url"
                .label=${0}
                @click=${0}
                .path=${0}
              ></ha-icon-button>
            </div>
          </div>
          <div class="instance-detail">
            <span>
              ${0}:
            </span>
            <span>
              ${0}
            </span>
          </div>
        </div>
        <ha-alert
          alert-type="info"
          .title=${0}
        >
          ${0}
        </ha-alert>

        <ha-button
          appearance="plain"
          @click=${0}
          slot="secondaryAction"
        >
          ${0}
        </ha-button>
        <ha-button @click=${0} slot="primaryAction">
          ${0}
        </ha-button>
      </ha-dialog>
    `),this.closeDialog,(0,_.l)(this.hass,this.hass.localize("ui.panel.config.cloud.dialog_already_connected.heading")),this.hass.localize("ui.panel.config.cloud.dialog_already_connected.description"),this.hass.localize("ui.panel.config.cloud.dialog_already_connected.other_home_assistant"),a.name?(0,d.qy)(b||(b=A`<div class="instance-detail">
                <span>
                  ${0}:
                </span>
                <span>${0}</span>
              </div>`),this.hass.localize("ui.panel.config.cloud.dialog_already_connected.instance_name"),a.name):d.s6,a.version?(0,d.qy)(m||(m=A`<div class="instance-detail">
                <span>
                  ${0}:
                </span>
                <span>${0}</span>
              </div>`),this.hass.localize("ui.panel.config.cloud.dialog_already_connected.instance_version"),a.version):d.s6,this.hass.localize("ui.panel.config.cloud.dialog_already_connected.ip_address"),this._obfuscateIp?(0,f.w)(a.remote_ip_address):a.remote_ip_address,this.hass.localize("ui.panel.config.cloud.dialog_already_connected.obfuscated_ip."+(this._obfuscateIp?"hide":"show")),this._toggleObfuscateIp,this._obfuscateIp?"M12,9A3,3 0 0,0 9,12A3,3 0 0,0 12,15A3,3 0 0,0 15,12A3,3 0 0,0 12,9M12,17A5,5 0 0,1 7,12A5,5 0 0,1 12,7A5,5 0 0,1 17,12A5,5 0 0,1 12,17M12,4.5C7,4.5 2.73,7.61 1,12C2.73,16.39 7,19.5 12,19.5C17,19.5 21.27,16.39 23,12C21.27,7.61 17,4.5 12,4.5Z":"M11.83,9L15,12.16C15,12.11 15,12.05 15,12A3,3 0 0,0 12,9C11.94,9 11.89,9 11.83,9M7.53,9.8L9.08,11.35C9.03,11.56 9,11.77 9,12A3,3 0 0,0 12,15C12.22,15 12.44,14.97 12.65,14.92L14.2,16.47C13.53,16.8 12.79,17 12,17A5,5 0 0,1 7,12C7,11.21 7.2,10.47 7.53,9.8M2,4.27L4.28,6.55L4.73,7C3.08,8.3 1.78,10 1,12C2.73,16.39 7,19.5 12,19.5C13.55,19.5 15.03,19.2 16.38,18.66L16.81,19.08L19.73,22L21,20.73L3.27,3M12,7A5,5 0 0,1 17,12C17,12.64 16.87,13.26 16.64,13.82L19.57,16.75C21.07,15.5 22.27,13.86 23,12C21.27,7.61 17,4.5 12,4.5C10.6,4.5 9.26,4.75 8,5.2L10.17,7.35C10.74,7.13 11.35,7 12,7Z",this.hass.localize("ui.panel.config.cloud.dialog_already_connected.connected_at"),(0,u.r6)(new Date(a.connected_at),this.hass.locale,this.hass.config),this.hass.localize("ui.panel.config.cloud.dialog_already_connected.info_backups.title"),this.hass.localize("ui.panel.config.cloud.dialog_already_connected.info_backups.description"),this.closeDialog,this.hass.localize("ui.common.cancel"),this._logInHere,this.hass.localize("ui.panel.config.cloud.dialog_already_connected.login_here"))}},{key:"_toggleObfuscateIp",value:function(){this._obfuscateIp=!this._obfuscateIp}},{key:"_logInHere",value:function(){var a,e;null===(a=this._params)||void 0===a||null===(e=a.logInHereAction)||void 0===e||e.call(a),this.closeDialog()}}],[{key:"styles",get:function(){return[g.nA,(0,d.AH)($||($=A`
        ha-dialog {
          --mdc-dialog-max-width: 535px;
        }
        .intro b {
          display: block;
          margin-top: 16px;
        }
        .instance-details {
          display: flex;
          flex-direction: column;
          margin-bottom: 16px;
        }
        .instance-detail {
          display: flex;
          flex-direction: row;
          justify-content: space-between;
          align-items: center;
        }
        .obfuscated {
          align-items: center;
          display: flex;
          flex-direction: row;
        }
      `))]}}])}(d.WF);(0,c.__decorate)([(0,r.wk)()],k.prototype,"_params",void 0),(0,c.__decorate)([(0,r.wk)()],k.prototype,"_obfuscateIp",void 0),k=(0,c.__decorate)([(0,r.EM)("dialog-cloud-already-connected")],k),n()}catch(C){n(C)}}))},91550:function(a,e,i){i.d(e,{w:function(){return n}});i(27495),i(25440);function n(a){return a.endsWith(".ui.nabu.casa")?"https://•••••••••••••••••.ui.nabu.casa":a.replace(/(?<=:\/\/)[\w-]+|(?<=\.)[\w-]+/g,(a=>"•".repeat(a.length)))}}}]);
//# sourceMappingURL=8547.e9758bc1face41b7.js.map