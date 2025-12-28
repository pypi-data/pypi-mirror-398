import{L as E,N as t,M as U,a0 as l,a1 as I,O as q,d as Y,bB as W,q as n,a3 as g,P as be,a4 as fe,T as ve,U as G,bC as ge,ao as we,b as K,A as me,an as pe,m as z,X as w,C as j,B as s,Y as ye,aq as M,bk as ke,bD as xe,c as Se,bm as L,bn as A,bo as H,bq as _e,bv as X,o as $e}from"./index-BXlMPVIj.js";import{N as Be}from"./Space-Vtp1f_sA.js";const Ce=E("switch",`
 height: var(--n-height);
 min-width: var(--n-width);
 vertical-align: middle;
 user-select: none;
 -webkit-user-select: none;
 display: inline-flex;
 outline: none;
 justify-content: center;
 align-items: center;
`,[t("children-placeholder",`
 height: var(--n-rail-height);
 display: flex;
 flex-direction: column;
 overflow: hidden;
 pointer-events: none;
 visibility: hidden;
 `),t("rail-placeholder",`
 display: flex;
 flex-wrap: none;
 `),t("button-placeholder",`
 width: calc(1.75 * var(--n-rail-height));
 height: var(--n-rail-height);
 `),E("base-loading",`
 position: absolute;
 top: 50%;
 left: 50%;
 transform: translateX(-50%) translateY(-50%);
 font-size: calc(var(--n-button-width) - 4px);
 color: var(--n-loading-color);
 transition: color .3s var(--n-bezier);
 `,[q({left:"50%",top:"50%",originalTransform:"translateX(-50%) translateY(-50%)"})]),t("checked, unchecked",`
 transition: color .3s var(--n-bezier);
 color: var(--n-text-color);
 box-sizing: border-box;
 position: absolute;
 white-space: nowrap;
 top: 0;
 bottom: 0;
 display: flex;
 align-items: center;
 line-height: 1;
 `),t("checked",`
 right: 0;
 padding-right: calc(1.25 * var(--n-rail-height) - var(--n-offset));
 `),t("unchecked",`
 left: 0;
 justify-content: flex-end;
 padding-left: calc(1.25 * var(--n-rail-height) - var(--n-offset));
 `),U("&:focus",[t("rail",`
 box-shadow: var(--n-box-shadow-focus);
 `)]),l("round",[t("rail","border-radius: calc(var(--n-rail-height) / 2);",[t("button","border-radius: calc(var(--n-button-height) / 2);")])]),I("disabled",[I("icon",[l("rubber-band",[l("pressed",[t("rail",[t("button","max-width: var(--n-button-width-pressed);")])]),t("rail",[U("&:active",[t("button","max-width: var(--n-button-width-pressed);")])]),l("active",[l("pressed",[t("rail",[t("button","left: calc(100% - var(--n-offset) - var(--n-button-width-pressed));")])]),t("rail",[U("&:active",[t("button","left: calc(100% - var(--n-offset) - var(--n-button-width-pressed));")])])])])])]),l("active",[t("rail",[t("button","left: calc(100% - var(--n-button-width) - var(--n-offset))")])]),t("rail",`
 overflow: hidden;
 height: var(--n-rail-height);
 min-width: var(--n-rail-width);
 border-radius: var(--n-rail-border-radius);
 cursor: pointer;
 position: relative;
 transition:
 opacity .3s var(--n-bezier),
 background .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier);
 background-color: var(--n-rail-color);
 `,[t("button-icon",`
 color: var(--n-icon-color);
 transition: color .3s var(--n-bezier);
 font-size: calc(var(--n-button-height) - 4px);
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 display: flex;
 justify-content: center;
 align-items: center;
 line-height: 1;
 `,[q()]),t("button",`
 align-items: center; 
 top: var(--n-offset);
 left: var(--n-offset);
 height: var(--n-button-height);
 width: var(--n-button-width-pressed);
 max-width: var(--n-button-width);
 border-radius: var(--n-button-border-radius);
 background-color: var(--n-button-color);
 box-shadow: var(--n-button-box-shadow);
 box-sizing: border-box;
 cursor: inherit;
 content: "";
 position: absolute;
 transition:
 background-color .3s var(--n-bezier),
 left .3s var(--n-bezier),
 opacity .3s var(--n-bezier),
 max-width .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier);
 `)]),l("active",[t("rail","background-color: var(--n-rail-color-active);")]),l("loading",[t("rail",`
 cursor: wait;
 `)]),l("disabled",[t("rail",`
 cursor: not-allowed;
 opacity: .5;
 `)])]),Re=Object.assign(Object.assign({},G.props),{size:{type:String,default:"medium"},value:{type:[String,Number,Boolean],default:void 0},loading:Boolean,defaultValue:{type:[String,Number,Boolean],default:!1},disabled:{type:Boolean,default:void 0},round:{type:Boolean,default:!0},"onUpdate:value":[Function,Array],onUpdateValue:[Function,Array],checkedValue:{type:[String,Number,Boolean],default:!0},uncheckedValue:{type:[String,Number,Boolean],default:!1},railStyle:Function,rubberBand:{type:Boolean,default:!0},onChange:[Function,Array]});let _;const Ve=Y({name:"Switch",props:Re,slots:Object,setup(e){_===void 0&&(typeof CSS<"u"?typeof CSS.supports<"u"?_=CSS.supports("width","max(1px)"):_=!1:_=!0);const{mergedClsPrefixRef:d,inlineThemeDisabled:m}=ve(e),o=G("Switch","-switch",Ce,ge,e,d),r=we(e),{mergedSizeRef:$,mergedDisabledRef:f}=r,k=K(e.defaultValue),B=me(e,"value"),v=pe(B,k),x=z(()=>v.value===e.checkedValue),p=K(!1),i=K(!1),c=z(()=>{const{railStyle:a}=e;if(a)return a({focused:i.value,checked:x.value})});function u(a){const{"onUpdate:value":C,onChange:R,onUpdateValue:V}=e,{nTriggerFormInput:F,nTriggerFormChange:N}=r;C&&M(C,a),V&&M(V,a),R&&M(R,a),k.value=a,F(),N()}function J(){const{nTriggerFormFocus:a}=r;a()}function Q(){const{nTriggerFormBlur:a}=r;a()}function Z(){e.loading||f.value||(v.value!==e.checkedValue?u(e.checkedValue):u(e.uncheckedValue))}function ee(){i.value=!0,J()}function te(){i.value=!1,Q(),p.value=!1}function ae(a){e.loading||f.value||a.key===" "&&(v.value!==e.checkedValue?u(e.checkedValue):u(e.uncheckedValue),p.value=!1)}function ie(a){e.loading||f.value||a.key===" "&&(a.preventDefault(),p.value=!0)}const O=z(()=>{const{value:a}=$,{self:{opacityDisabled:C,railColor:R,railColorActive:V,buttonBoxShadow:F,buttonColor:N,boxShadowFocus:ne,loadingColor:oe,textColor:re,iconColor:le,[w("buttonHeight",a)]:h,[w("buttonWidth",a)]:se,[w("buttonWidthPressed",a)]:de,[w("railHeight",a)]:b,[w("railWidth",a)]:S,[w("railBorderRadius",a)]:ce,[w("buttonBorderRadius",a)]:ue},common:{cubicBezierEaseInOut:he}}=o.value;let T,D,P;return _?(T=`calc((${b} - ${h}) / 2)`,D=`max(${b}, ${h})`,P=`max(${S}, calc(${S} + ${h} - ${b}))`):(T=j((s(b)-s(h))/2),D=j(Math.max(s(b),s(h))),P=s(b)>s(h)?S:j(s(S)+s(h)-s(b))),{"--n-bezier":he,"--n-button-border-radius":ue,"--n-button-box-shadow":F,"--n-button-color":N,"--n-button-width":se,"--n-button-width-pressed":de,"--n-button-height":h,"--n-height":D,"--n-offset":T,"--n-opacity-disabled":C,"--n-rail-border-radius":ce,"--n-rail-color":R,"--n-rail-color-active":V,"--n-rail-height":b,"--n-rail-width":S,"--n-width":P,"--n-box-shadow-focus":ne,"--n-loading-color":oe,"--n-text-color":re,"--n-icon-color":le}}),y=m?ye("switch",z(()=>$.value[0]),O,e):void 0;return{handleClick:Z,handleBlur:te,handleFocus:ee,handleKeyup:ae,handleKeydown:ie,mergedRailStyle:c,pressed:p,mergedClsPrefix:d,mergedValue:v,checked:x,mergedDisabled:f,cssVars:m?void 0:O,themeClass:y?.themeClass,onRender:y?.onRender}},render(){const{mergedClsPrefix:e,mergedDisabled:d,checked:m,mergedRailStyle:o,onRender:r,$slots:$}=this;r?.();const{checked:f,unchecked:k,icon:B,"checked-icon":v,"unchecked-icon":x}=$,p=!(W(B)&&W(v)&&W(x));return n("div",{role:"switch","aria-checked":m,class:[`${e}-switch`,this.themeClass,p&&`${e}-switch--icon`,m&&`${e}-switch--active`,d&&`${e}-switch--disabled`,this.round&&`${e}-switch--round`,this.loading&&`${e}-switch--loading`,this.pressed&&`${e}-switch--pressed`,this.rubberBand&&`${e}-switch--rubber-band`],tabindex:this.mergedDisabled?void 0:0,style:this.cssVars,onClick:this.handleClick,onFocus:this.handleFocus,onBlur:this.handleBlur,onKeyup:this.handleKeyup,onKeydown:this.handleKeydown},n("div",{class:`${e}-switch__rail`,"aria-hidden":"true",style:o},g(f,i=>g(k,c=>i||c?n("div",{"aria-hidden":!0,class:`${e}-switch__children-placeholder`},n("div",{class:`${e}-switch__rail-placeholder`},n("div",{class:`${e}-switch__button-placeholder`}),i),n("div",{class:`${e}-switch__rail-placeholder`},n("div",{class:`${e}-switch__button-placeholder`}),c)):null)),n("div",{class:`${e}-switch__button`},g(B,i=>g(v,c=>g(x,u=>n(be,null,{default:()=>this.loading?n(fe,{key:"loading",clsPrefix:e,strokeWidth:20}):this.checked&&(c||i)?n("div",{class:`${e}-switch__button-icon`,key:c?"checked-icon":"icon"},c||i):!this.checked&&(u||i)?n("div",{class:`${e}-switch__button-icon`,key:u?"unchecked-icon":"icon"},u||i):null})))),g(f,i=>i&&n("div",{key:"checked",class:`${e}-switch__checked`},i)),g(k,i=>i&&n("div",{key:"unchecked",class:`${e}-switch__unchecked`},i)))))}}),ze={style:{padding:"1rem"}},Te=Y({__name:"Setting",setup(e){const{is_debug:d}=ke(xe());return(m,o)=>($e(),Se("div",ze,[L(H(Be),{vertical:""},{default:A(()=>[L(H(Ve),{value:H(d),"onUpdate:value":o[0]||(o[0]=r=>_e(d)?d.value=r:null)},{checked:A(()=>[...o[1]||(o[1]=[X(" Debug mode ",-1)])]),unchecked:A(()=>[...o[2]||(o[2]=[X(" Debug mode ",-1)])]),_:1},8,["value"])]),_:1})]))}});export{Te as default};
