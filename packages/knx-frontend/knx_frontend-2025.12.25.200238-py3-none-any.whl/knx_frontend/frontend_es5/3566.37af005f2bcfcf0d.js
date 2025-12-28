"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["3566"],{60029:function(a,t,i){i.a(a,(async function(a,e){try{i.r(t),i.d(t,{HaImagecropperDialog:function(){return A}});var o=i(44734),r=i(56038),s=i(69683),p=i(6454),c=(i(28706),i(23792),i(26099),i(27495),i(25440),i(62953),i(3296),i(27208),i(48408),i(14603),i(47566),i(98721),i(62826)),n=i(23318),l=i.n(n),h=i(32609),u=i(96196),_=i(77845),d=i(94333),m=i(89473),g=(i(95637),i(39396)),v=a([m]);m=(v.then?(await v)():v)[0];var y,f,k,b=a=>a,A=function(a){function t(){var a;(0,o.A)(this,t);for(var i=arguments.length,e=new Array(i),r=0;r<i;r++)e[r]=arguments[r];return(a=(0,s.A)(this,t,[].concat(e)))._open=!1,a}return(0,p.A)(t,a),(0,r.A)(t,[{key:"showDialog",value:function(a){this._params=a,this._open=!0}},{key:"closeDialog",value:function(){var a;this._open=!1,this._params=void 0,null===(a=this._cropper)||void 0===a||a.destroy(),this._cropper=void 0,this._isTargetAspectRatio=!1}},{key:"updated",value:function(a){a.has("_params")&&this._params&&(this._cropper?this._cropper.replace(URL.createObjectURL(this._params.file)):(this._image.src=URL.createObjectURL(this._params.file),this._cropper=new(l())(this._image,{aspectRatio:this._params.options.aspectRatio,viewMode:1,dragMode:"move",minCropBoxWidth:50,ready:()=>{this._isTargetAspectRatio=this._checkMatchAspectRatio(),URL.revokeObjectURL(this._image.src)}})))}},{key:"_checkMatchAspectRatio",value:function(){var a,t=null===(a=this._params)||void 0===a?void 0:a.options.aspectRatio;if(!t)return!0;var i=this._cropper.getImageData();if(i.aspectRatio===t)return!0;if(i.naturalWidth>i.naturalHeight){var e=i.naturalWidth/t;return Math.abs(e-i.naturalHeight)<=1}var o=i.naturalHeight*t;return Math.abs(o-i.naturalWidth)<=1}},{key:"render",value:function(){var a;return(0,u.qy)(y||(y=b`<ha-dialog
      @closed=${0}
      scrimClickAction
      escapeKeyAction
      .open=${0}
    >
      <div
        class="container ${0}"
      >
        <img alt=${0} />
      </div>
      <ha-button
        appearance="plain"
        slot="primaryAction"
        @click=${0}
      >
        ${0}
      </ha-button>
      ${0}

      <ha-button slot="primaryAction" @click=${0}>
        ${0}
      </ha-button>
    </ha-dialog>`),this.closeDialog,this._open,(0,d.H)({round:Boolean(null===(a=this._params)||void 0===a?void 0:a.options.round)}),this.hass.localize("ui.dialogs.image_cropper.crop_image"),this.closeDialog,this.hass.localize("ui.common.cancel"),this._isTargetAspectRatio?(0,u.qy)(f||(f=b`<ha-button
            appearance="plain"
            slot="primaryAction"
            @click=${0}
          >
            ${0}
          </ha-button>`),this._useOriginal,this.hass.localize("ui.dialogs.image_cropper.use_original")):u.s6,this._cropImage,this.hass.localize("ui.dialogs.image_cropper.crop"))}},{key:"_cropImage",value:function(){this._cropper.getCroppedCanvas().toBlob((a=>{if(a){var t=new File([a],this._params.file.name,{type:this._params.options.type||this._params.file.type});this._params.croppedCallback(t),this.closeDialog()}}),this._params.options.type||this._params.file.type,this._params.options.quality)}},{key:"_useOriginal",value:function(){this._params.croppedCallback(this._params.file),this.closeDialog()}}],[{key:"styles",get:function(){return[g.nA,(0,u.AH)(k||(k=b`
        ${0}
        .container {
          max-width: 640px;
        }
        img {
          max-width: 100%;
        }
        .container.round .cropper-view-box,
        .container.round .cropper-face {
          border-radius: var(--ha-border-radius-circle);
        }
        .cropper-line,
        .cropper-point,
        .cropper-point.point-se::before {
          background-color: var(--primary-color);
        }
      `),(0,u.iz)(h))]}}])}(u.WF);(0,c.__decorate)([(0,_.MZ)({attribute:!1})],A.prototype,"hass",void 0),(0,c.__decorate)([(0,_.wk)()],A.prototype,"_params",void 0),(0,c.__decorate)([(0,_.wk)()],A.prototype,"_open",void 0),(0,c.__decorate)([(0,_.P)("img",!0)],A.prototype,"_image",void 0),(0,c.__decorate)([(0,_.wk)()],A.prototype,"_isTargetAspectRatio",void 0),A=(0,c.__decorate)([(0,_.EM)("image-cropper-dialog")],A),e()}catch(R){e(R)}}))}}]);
//# sourceMappingURL=3566.37af005f2bcfcf0d.js.map