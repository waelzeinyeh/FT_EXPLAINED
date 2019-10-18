import matplotlib
matplotlib.use("WebAgg")
matplotlib.rcParams['animation.embed_limit'] = 2**128
matplotlib.rcParams["savefig.dpi"]=100
from matplotlib.figure import Figure
from matplotlib.patches import ConnectionPatch
from matplotlib.animation import FuncAnimation
import numpy as np
import random
import base64
from io import BytesIO
from flask import Flask, render_template, request, session




#####################################################################################


def del_freq():

    session["freq_nb"]=0
    session["FT_step"]=0
    session["seed"]=random.randint(1,100)

    if session["msg_check"]=="Messages:On":
        session["message"]="""When hydrogen nuclei (protons) in a molecule placed in a magnetic field are excited with a radiofrequency pulse, they can induce a current in the receiver coil, which leads to a radiofrequency signal (the resonance signal). This resonance signal will decay because of spin-spin relaxation.

<br><br>The frequency of each resonance depends on the chemical environment of the proton.<br><br>

In a 400 MHz spectrometer, these resonances scale between (400 MHz - 5 ppm) and (400 MHz + 5 ppm) approximately, which is between 399’998’000 Hz and 400’002’000 Hz.<br><br>

To improve clarity in this application, we will imagine that resonances scale from {} to {} Hz.<br><br>

You can start adding protons by choosing a frequency and clicking on the Add Frequency button above.<br>""".format(session["freq_min"],session["freq_max"])



#####################################################################################



def init_app():

    font = {'size':10}
    matplotlib.rc('font', **font)
    session["msg_check"]="Messages:On"
    session["acq_time"]=5
    session["freq_min"]=1
    session["freq_max"]=10
    session["freq_show"]=int(random.random()*(session["freq_max"]-session["freq_min"])+session["freq_min"])
    session["freq_res"]=0.1
    session["decay"]=1.
    session["trace_every"]=0.5
    session["time_delay"]=1
    session["phase"]=0.
    delta=1/(2*(session["freq_max"]+1))
    session["nb_points"]=int(session["acq_time"]/delta)
    if session["nb_points"]<500:
        session["nb_points"]=500
    session["frequency"]=[0,0,0,0]
    session["noise"]=0.
    session["FT_step"]=0

    del_freq()

#####################################################################################



def draw_freq():

    t=np.linspace(0,session["acq_time"],session["nb_points"])
    resonance=np.zeros((4,session["nb_points"]))

    fig=Figure(dpi=100,figsize=(9,6.75))
    fig.subplots_adjust(wspace=0.5, hspace=0.5)

    ax_one=fig.add_subplot(2,2,1)
    ax_one.set_ylim(-1.1,1.1)
    ax_one.set_xlim(0,session["acq_time"])
    ax_one.set_xlabel("Time (s)",x=0.9)
    ax_one.set_ylabel("Amplitude",y=0.8)
    ax_one.set_title("1. One proton resonances")
    ax_one.tick_params(axis='y',which='both',left=True,labelleft=True)


    ax_FID=fig.add_subplot(2,2,2,sharex=ax_one)
    ax_FID.tick_params(axis='y',which='both',left=True,labelleft=True)
    ax_FID.set_title("2. FID (sum of all resonances)")
    ax_FID.set_xlabel("Time (s)",x=0.9)
    ax_FID.set_ylabel("Amplitude",y=0.8)
    ax_FID.set_ylim(-1.1,1.1)
    ax_FID.set_xlim(0,session["acq_time"])


    ax_mult=fig.add_subplot(2,2,4,sharex=ax_one)
    ax_mult.set_ylim(-1.1,1.1)
    ax_mult.set_xlim(0,session["acq_time"])
    ax_mult.set_xlabel("Time (s)",x=0.9)
    ax_mult.set_ylabel("Amplitude",y=0.8)
    ax_mult.set_title("3. FID * Trial Frequency")
    ax_mult.tick_params(axis='y',which='both',left=True,labelleft=True)

    ax_FT=fig.add_subplot(2,2,3)
    ax_FT.set_xlim(session["freq_max"]+1,session["freq_min"]-1)
    ax_FT.set_ylim(-0.1,0.5)
    ax_FT.set_xlabel("Frequency (Hz)",x=0.9)
    ax_FT.set_ylabel("Relative Intensity",y=0.8)
    ax_FT.set_title("4. Spectrum")
    ax_FT.tick_params(axis='y',which='both',left=True,labelleft=True)
    ax_FT.grid(b=True,linestyle="--",which="both")

    colors=["green","black","red","cyan"]
    FID=np.zeros(session["nb_points"])

    if session["freq_nb"]==0:
        return t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT

    for n in range(0,session["freq_nb"]):
        resonance[n]=np.cos(2*np.pi*session["frequency"][n]*t+session["phase"]*np.pi)*np.exp(-t/session["decay"])
        FID=FID+resonance[n]
        ax_one.plot(t,resonance[n],linewidth=1,color=colors[n],label="Proton {} : {} Hz".format(n+1,int(session["frequency"][n])),alpha=0.5)
    ax_one.legend(loc=1)

    con_1 = ConnectionPatch(xyA=(1.2,0.5), xyB=(-0.2,0.5), coordsA="axes fraction", coordsB="axes fraction",axesA=ax_one, axesB=ax_FID,color="red")
    con_1.set_arrowstyle("simple",head_length=0.5, head_width=1, tail_width=0.3)
    ax_one.add_patch(con_1)

    np.random.seed(session["seed"])
    FID=FID+np.random.normal(0, session["noise"]/100/2*(max(FID)-min(FID))/2, size=session["nb_points"])
    ax_FID.plot(t,FID,linewidth=1,color="blue")
    ax_FID.legend(["FID"],loc=1)
    if max(FID)>-min(FID):
        ax_mult.set_ylim(-max(FID)*1.1,max(FID)*1.1)
        ax_FID.set_ylim(-max(FID)*1.1,max(FID)*1.1)
    else:
        ax_mult.set_ylim(min(FID)*1.1,-min(FID)*1.1)
        ax_FID.set_ylim(min(FID)*1.1,-min(FID)*1.1)
    if session["msg_check"]=="Messages:On":
        session["message"]="""More proton frequencies (up to 4) can be added using the same procedure.<br/><br/>

In graph 2, you will see the FID (Free Induction Decay) getting updated to correspond to the sum of all signals entered.<br/><br/>When this is done, proceed to the next step by clicking on Fourier Transform button.<br/>"""
    else:
        session["message"]=""
    return t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT



#####################################################################################



def new_freq():

    if session["freq_nb"]==4:
        session["FT_step"]=0
        t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT=draw_freq()
        session["message"]="The app is limited to 4 frequencies in order to avoid crowding the display.<br>"
        return fig
    try:
        freq_input=int(float(request.form["freq"]))
        if freq_input>session["freq_max"] or freq_input<session["freq_min"]:
            session["FT_step"]=0
            if session["freq_nb"]!=0:
                t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT=draw_freq()
                session["message"]="The new frequency must be an integer between {} and {} Hz.<br>".format(session["freq_min"],session["freq_max"])
                return fig
            else:
                return
    except:
        session["FT_step"]=0
        if session["freq_nb"]!=0:
            t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT=draw_freq()
            session["message"]="The new frequency must be an integer between {} and {} Hz.<br>".format(session["freq_min"],session["freq_max"])
            return fig
        else:
            session["message"]="The new frequency must be an integer between {} and {} Hz.<br>".format(session["freq_min"],session["freq_max"])
            return

    session["frequency"][session["freq_nb"]]=freq_input
    session["freq_nb"]+=1
    t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT=draw_freq()
    session["FT_step"]=0
    session["freq_show"]=int(random.random()*(session["freq_max"]-session["freq_min"])+session["freq_min"])
    return fig



#####################################################################################




def animate(f,t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n):

    for elem in reversed(ax_mult.collections+ax_mult.lines+ax_FID.lines+ax_FT.lines):
        elem.remove()
    ax_FID.plot(t,FID,linewidth=1,color="blue")
    ax_FID.plot(t,trial[f],linewidth=1,color="magenta",alpha=0.5)
    ax_mult.fill_between(t,mult[f],where=mult[f]>0,interpolate=True,color="blue",label="Positive Areas {}".format(round(posinteg[f],3)))
    ax_mult.fill_between(t,mult[f],where=mult[f]<0,interpolate=True,color="red",label="Negative Areas {}".format(round(neginteg[f],3)))
    ax_mult.legend()
    ax_FID.legend(("FID","Trial Frequency {} Hz".format(round(freqs[f],1))),loc=1)
    ax_FT.plot(freqs[:f+1],integ[:f+1],linewidth=1,color="blue")
    ax_FT.legend(["""Trial frequency {} Hz\nTotal area {}""".format(round(freqs[f],1),round(round(posinteg[f],3)+round(neginteg[f],3),3))],loc=1,handlelength=0)





#####################################################################################


def step_1():

    t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT=draw_freq()
    con_2 = ConnectionPatch(xyA=(0.5,-0.2), xyB=(0.5,1.15), coordsA="axes fraction", coordsB="axes fraction",axesA=ax_FID, axesB=ax_mult,color="red")
    con_2.set_arrowstyle("simple",head_length=0.5, head_width=1, tail_width=0.3)
    ax_FID.add_patch(con_2)


    freqs=np.arange(session["freq_min"]-1,session["freq_max"]+1,session["freq_res"])
    freqs=np.append(freqs,session["freq_max"]+1)
    nb_freq=freqs.size
    trial=np.zeros((nb_freq,session["nb_points"]))
    mult=np.zeros((nb_freq,session["nb_points"]))
    integ=np.zeros(nb_freq)
    posinteg=np.zeros(nb_freq)
    neginteg=np.zeros(nb_freq)

    for i,freq in enumerate(freqs):
        trial[i]=np.cos(2*np.pi*freq*t)
        mult[i]=trial[i]*FID
        posmult=np.zeros(session["nb_points"])
        negmult=np.zeros(session["nb_points"])
        for nn,ii in enumerate(mult[i]):
            if ii >0:
                posmult[nn]=ii
            if ii <0:
                negmult[nn]=ii
        posinteg[i]=np.trapz(posmult,t)
        neginteg[i]=np.trapz(negmult,t)
        integ[i]=np.trapz(mult[i],t)
        if freq<=session["freq_min"]:
            n=i
    ax_FT.set_ylim(integ.min()-(integ.max()-integ.min())*0.05,integ.max()+(integ.max()-integ.min())*0.4)


    ax_FID.plot(t,trial[n],linewidth=1,color="magenta",alpha=0.5)
    ax_mult.plot(t,mult[n],linewidth=1,color="black",alpha=0.5)
    ax_FID.legend(("FID","Trial Frequency {} Hz".format(round(freqs[n],1))),loc=1)
    session["message"]="""The acquired signal will be processed and the computer will try to find all the frequencies from which your FID is composed.<br><br>

To do this, it will multiply your FID by cosine functions with increasing frequencies, covering all our frequencies range from {} to {} Hz.<br>

We will call these cosine functions "Trial Frequencies".<br><br>

The multiplication is done "point by point", as shown in the example below: <br><br>

<img src="/static/img1.png" style="width:95%"/><br><br>

The result of the multiplication of your FID by the trial frequency {} Hz is shown in graph 3.<br>

<input type=submit name="msgOK" value="Next" class="control">""".format(session["freq_min"],session["freq_max"],round(freqs[n],1))

    session["FT_step"]=1
    return t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n


#####################################################################################


def step_2(t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n):
    for elem in reversed(ax_mult.lines):
        elem.remove()
    ax_mult.fill_between(t,mult[n],where=mult[n]>0,interpolate=True,color="blue",label="Positive Areas {}".format(round(posinteg[n],3)))
    ax_mult.fill_between(t,mult[n],where=mult[n]<0,interpolate=True,color="red",label="Negative Areas {}".format(round(neginteg[n],3)))
    if ax_mult.get_legend() is None:
        ax_mult.legend(loc=1)
    session["message"]="""Next, the area under the multiplication curve is calculated.<br><br>

If the trial frequency corresponds to one of the frequencies of the protons in the FID, the multiplication curve will be always positive, because the trial frequency and the FID will be positive or negative at the same time, as shown in the example below: <br><br>

<img src="/static/img2.png" style="width:95%"/><br><br>

In this case, the total area under the curve will be positive.<br>

<input type=submit name="msgOK" value="Next" class="control">"""

    session["FT_step"]=2
    return t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n



#####################################################################################



def step_3(t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n):

    ax_mult.fill_between(t,mult[n],where=mult[n]>0,interpolate=True,color="blue",label="Positive Areas")
    ax_mult.fill_between(t,mult[n],where=mult[n]<0,interpolate=True,color="red",label="Negative Areas")
    if ax_mult.get_legend() is None:
        ax_mult.legend(loc=1)
    session["message"]="""Otherwise, if the trial frequency doesn't correspond to any hidden frequency in your FID, the multiplication curve will regularly oscillate between positive and negative values.<br>

This is shown in the example below:<br><br>

<img src="/static/img3.png" style="width:95%"/><br><br>

In this case, the total area under the curve (blue+red) will be very close to zero, because of the oscillation of the curve between positive and negative values.

<br><input type=submit name="msgOK" value="Next" class="control">"""

    session["FT_step"]=3
    return t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n

#####################################################################################



def step_4(t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n):

    con_3 = ConnectionPatch(xyB=(1.2,0.5), xyA=(-0.2,0.5), coordsA="axes fraction", coordsB="axes fraction",axesA=ax_mult, axesB=ax_FT,color="red")
    con_3.set_arrowstyle("simple",head_length=0.5, head_width=1, tail_width=0.3)
    ax_mult.add_patch(con_3)

    ax_mult.fill_between(t,mult[n],where=mult[n]>0,interpolate=True,color="blue",label="Positive Areas")
    ax_mult.fill_between(t,mult[n],where=mult[n]<0,interpolate=True,color="red",label="Negative Areas")
    if ax_mult.get_legend() is None:
        ax_mult.legend(loc=1)
    ax_FT.plot(freqs[:n+1],integ[:n+1],linewidth=1,color="blue")
    ax_FT.plot([freqs[n]],[integ[n]],"ro")
    ann=ax_FT.annotate("Trial frequency {} Hz\nTotal area {}".format(round(freqs[n],1),round(round(posinteg[n],3)+round(neginteg[n],3),3)), xy=(freqs[n],integ[n]), xycoords='data',
            xytext=(-25, 10), textcoords='offset points',
            arrowprops=dict(facecolor='black',shrink=0.1,width=2,headwidth=10),
            horizontalalignment='right', verticalalignment='bottom')
    session["message"]="""The area under the multiplication curve (over the acquisition time) for a given trial frequency represents the relative intensity of the signal at this frequency.<br><br>

For instance, the calculation for the trial frequency {} Hz from your FID gives (see graph 3):<br><br>

<div style="background-color:white;font-weight:bold">Total area ( = Relative intensity) = <br><span style="color:blue">Positive areas</span> + <span style="color:red">Negative areas </span>= <span style="color:blue">({})</span> + <span style="color:red">({})</span> = {} area units</div><br>

This point is reported on the final spectrum presented in graph 4.<br><br>

The computer will repeat this operation with trial frequencies from {} to {} Hz in order to cover all our range of frequencies.<br><br>

Press OK to access the spectrum generation (loading of the animation can take up to 1 min).<br><input type=submit name="msgOK" value="OK" class="control">""".format(round(freqs[n],1),round(posinteg[n],3),round(neginteg[n],3),round(round(posinteg[n],3)+round(neginteg[n],3),3),session["freq_min"]-1,session["freq_max"]+1)

    session["FT_step"]=4
    return t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n,ann


#####################################################################################


def step_5(t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n,ann):
    ax_mult.fill_between([],[],color="blue",label="Positive Areas")
    ax_mult.fill_between([],[],color="red",label="Negative Areas")

    if ax_mult.get_legend() is None:
        ax_mult.legend(loc=1)
    con_3 = ConnectionPatch(xyB=(1.2,0.5), xyA=(-0.2,0.5), coordsA="axes fraction", coordsB="axes fraction",axesA=ax_mult, axesB=ax_FT,color="red")
    con_3.set_arrowstyle("simple",head_length=0.5, head_width=1, tail_width=0.3)
    ax_mult.add_patch(con_3)
    freq_range=np.arange(0, nb_freq-1, int(nb_freq*session["trace_every"]/(session["freq_max"]-session["freq_min"]+2)))
    freq_range=np.append(freq_range,nb_freq-1)
    if ann is not None:ann.remove()
    anim=FuncAnimation(fig, animate, frames=freq_range, fargs=(t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n),interval=session["time_delay"]*1000,blit=False,repeat=False)
    movie_data=anim.to_jshtml()
    session["message"]="""You can use the controls below the graph to see the animation.<br><br>
When you finish, we invite you to click on Parameters button. From there, you will be able to tune some parameters and observe the effect on your spectrum.<br>"""
    session["FT_step"]=5
    return movie_data



#####################################################################################

def new_param(t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT):
    try:
        if int(float(request.form["freq_max"]))>int(float(request.form["freq_min"])) and\
            int(float(request.form["freq_max"]))>0 and int(float(request.form["freq_max"]))<=20 and int(float(request.form["freq_min"]))>0 and \
            float(request.form["decay"])>0 and int(float(request.form["acq_time"]))>0 and int(float(request.form["acq_time"]))<=10 and \
            float(request.form["trace_every"])>=0.1 and float(request.form["noise"])<=100 and float(request.form["noise"])>=0:

            session["freq_min"]=int(float(request.form["freq_min"]))
            session["freq_max"]=int(float(request.form["freq_max"]))
            session["acq_time"]=int(float(request.form["acq_time"]))
            session["decay"]=float(request.form["decay"])
            session["trace_every"]=float(request.form["trace_every"])
            delta=1/(2*(session["freq_max"]+1))
            session["nb_points"]=int(session["acq_time"]/delta)
            if session["nb_points"]<500:
                session["nb_points"]=500
            session["phase"]=float(request.form["phase"])
            session["noise"]=float(request.form["noise"])
            if session["freq_nb"]!=0:
                draw_freq()
            ax_one.set_xlim(0,session["acq_time"])
            ax_FID.set_xlim(0,session["acq_time"])
            ax_mult.set_xlim(0,session["acq_time"])
            ax_FT.set_xlim(session["freq_max"]+1,session["freq_min"]-1)

            for n in range(0,session["freq_nb"]):
                if session["frequency"][n]<session["freq_min"] or session["frequency"][n]>session["freq_max"]:
                    del_freq()
                    break
            session["p_message"]=""
            return True

        else:
            session["p_message"]="""Invalid entries !"""
            return False
    except:
        session["p_message"]="""Invalid entries !"""
        return False


#####################################################################################



def save_fig(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png")
    image_data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return image_data



#####################################################################################

app = Flask(__name__)
app.config['SECRET_KEY'] = 'anaismibernamejbaytonouhadkodeserri'

@app.route('/', methods=['GET', 'POST'])

def index():

    if request.method == 'GET':
        return render_template("welcome.html")
    else:
        if "enter_app" in request.form:
            init_app()
            return render_template("index.html",msg_check=session["msg_check"],freq_min=session["freq_min"],freq_max=session["freq_max"],freq_show=session["freq_show"],message=session["message"])
        if "show_msg" in request.form:
            session["message"]=""
            if session["msg_check"]=="Messages:On":
                session["msg_check"]="Messages:Off"
            else:
                session["msg_check"]="Messages:On"
            if session["freq_nb"]!=0:
                t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT=draw_freq()
                image_data=save_fig(fig)
                return render_template("index.html",msg_check=session["msg_check"],freq_min=session["freq_min"], freq_max=session["freq_max"],freq_show=session["freq_show"], image_data=image_data,message=session["message"])
            else:
                del_freq()
                return render_template("index.html",msg_check=session["msg_check"],freq_min=session["freq_min"], freq_max=session["freq_max"],freq_show=session["freq_show"],message=session["message"])


        elif "add_freq" in request.form:
            fig=new_freq()
            if session["freq_nb"]!=0:
                image_data=save_fig(fig)
            else:
                image_data=""
            return render_template("index.html",msg_check=session["msg_check"],freq_min=session["freq_min"], freq_max=session["freq_max"],freq_show=session["freq_show"],message=session["message"],image_data=image_data)


        elif "ft" in request.form:
            if session["freq_nb"]!=0:
                session["FT_step"]=0
                if session["msg_check"]=="Messages:On":
                    t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n=step_1()
                    image_data=save_fig(fig)
                    return render_template("index.html",msg_check=session["msg_check"],freq_min=session["freq_min"], freq_max=session["freq_max"],freq_show=session["freq_show"],image_data=image_data,message=session["message"])
                else:
                    t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n=step_1()
                    ann=None
                    movie_data=step_5(t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n,ann)
                    return render_template("index.html",msg_check=session["msg_check"],freq_min=session["freq_min"],freq_max=session["freq_max"],freq_show=session["freq_show"],movie_data=movie_data)

            elif session["freq_nb"]==0:
                return render_template("index.html",msg_check=session["msg_check"],freq_min=session["freq_min"], freq_max=session["freq_max"],freq_show=session["freq_show"],message=session["message"])



        elif "del_freq" in request.form:
            session["message"]=""
            del_freq()
            return render_template("index.html",msg_check=session["msg_check"],freq_min=session["freq_min"], freq_max=session["freq_max"],freq_show=session["freq_show"],message=session["message"])


        elif "param" in request.form:
            return render_template("param.html",msg_check=session["msg_check"],freq_min=session["freq_min"],freq_max=session["freq_max"],freq_show=session["freq_show"],acq_time=session["acq_time"],decay=session["decay"],phase=session["phase"],noise=session["noise"],time_delay=session["time_delay"],trace_every=session["trace_every"])


        elif "paramOK" in request.form:
            t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT=draw_freq()
            param_valid=new_param(t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT)
            if param_valid:
                if session["freq_nb"]!=0:
                    if session["FT_step"]!=0:
                        session["message"]=""
                    session["FT_step"]=0
                    session["freq_show"]=int(random.random()*(session["freq_max"]-session["freq_min"])+session["freq_min"])
                    t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT=draw_freq()
                    image_data=save_fig(fig)
                    return render_template("index.html",msg_check=session["msg_check"],freq_min=session["freq_min"], freq_max=session["freq_max"],freq_show=session["freq_show"], image_data=image_data,message=session["message"])
                else:
                    session["freq_show"]=int(random.random()*(session["freq_max"]-session["freq_min"])+session["freq_min"])
                    del_freq()
                    return render_template("index.html",msg_check=session["msg_check"],freq_min=session["freq_min"], freq_max=session["freq_max"],freq_show=session["freq_show"],message=session["message"])
            else:
                return render_template("param.html",p_message=session["p_message"],freq_min=session["freq_min"],freq_max=session["freq_max"],freq_show=session["freq_show"],acq_time=session["acq_time"],decay=session["decay"],phase=session["phase"],noise=session["noise"],time_delay=session["time_delay"],trace_every=session["trace_every"])


        elif "paramCancel" in request.form or "return_app" in request.form:
            if session["freq_nb"]!=0:
                if session["FT_step"]!=0:
                    session["message"]=""
                session["FT_step"]=0
                t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT=draw_freq()
                image_data=save_fig(fig)
                return render_template("index.html",msg_check=session["msg_check"],freq_min=session["freq_min"], freq_max=session["freq_max"],freq_show=session["freq_show"],message=session["message"],image_data=image_data)
            else:
                return render_template("index.html",msg_check=session["msg_check"],freq_min=session["freq_min"], freq_max=session["freq_max"],freq_show=session["freq_show"],message=session["message"])


        elif "msgOK" in request.form:
            session["message"]=""

            if session["FT_step"]==1:
                t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n=step_1()
                t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n=step_2(t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n)
                image_data=save_fig(fig)
                return render_template("index.html",msg_check=session["msg_check"],freq_min=session["freq_min"], freq_max=session["freq_max"],freq_show=session["freq_show"],message=session["message"], image_data=image_data)


            elif session["FT_step"]==2:
                t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n=step_1()
                t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n=step_2(t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n)
                t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n=step_3(t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n)
                image_data=save_fig(fig)
                return render_template("index.html",msg_check=session["msg_check"],freq_min=session["freq_min"], freq_max=session["freq_max"],freq_show=session["freq_show"],message=session["message"], image_data=image_data)

            elif session["FT_step"]==3:
                t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n=step_1()
                t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n=step_2(t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n)
                t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n=step_3(t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n)
                t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n,ann=step_4(t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n)
                image_data=save_fig(fig)
                return render_template("index.html",msg_check=session["msg_check"],freq_min=session["freq_min"], freq_max=session["freq_max"],freq_show=session["freq_show"],message=session["message"], image_data=image_data)

            elif session["FT_step"]==4:
                t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n=step_1()
                t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n=step_2(t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n)
                t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n=step_3(t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n)
                t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n,ann=step_4(t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n)
                movie_data=step_5(t,resonance,FID,fig,ax_one,ax_FID,ax_mult,ax_FT,freqs,nb_freq,trial,mult,integ,posinteg,neginteg,n,ann)
                return render_template("index.html",msg_check=session["msg_check"],freq_min=session["freq_min"], freq_max=session["freq_max"],freq_show=session["freq_show"],message=session["message"], movie_data=movie_data)

        elif "freq_min_info" in request.form or "freq_max_info" in request.form:
            session['info_message']="""These are the minimum and maximum frequencies you are allowed to enter.<br>
            The maximum frequency in this app was limited to 20Hz in order to avoid excessive calculation time."""
            return render_template("param.html",info_message=session['info_message'],freq_min=session["freq_min"],freq_max=session["freq_max"],freq_show=session["freq_show"],acq_time=session["acq_time"],decay=session["decay"],phase=session["phase"],noise=session["noise"],time_delay=session["time_delay"],trace_every=session["trace_every"])

        elif "acq_time_info" in request.form:
            session['info_message']="""The acquisition time is the time during which the FID is recorded by the spectrometer. A sufficient acquisition time (about 3 times the decay constant) is needed to generate beautiful peaks after the Fourier transform.<br/><br/>
            However, be careful in case you have a lot of noise in your FID, because a long acquisition time will record only the noise after the signal has decayed, and the resulting spectrum will be noisier.<br><br>
            The maximum acquisition time was limited to 10s in this app in order to avoid excessive calculation time."""
            return render_template("param.html",info_message=session['info_message'],freq_min=session["freq_min"],freq_max=session["freq_max"],freq_show=session["freq_show"],acq_time=session["acq_time"],decay=session["decay"],phase=session["phase"],noise=session["noise"],time_delay=session["time_delay"],trace_every=session["trace_every"])

        elif "decay_info" in request.form:
            session['info_message']="""The decay constant depends on the nucleus type and on its environment. Typical values for protons are about 0.5-1 second.<br><br>
            The decay constant determines the speed of the resonance signal decay: After 1 decay constant, the signal loses 63% of its initial intensity.<br><br>
            The decay constant also determines the width of spectrum peaks after the Fourier transform : a long decay constant results in a narrow peak."""
            return render_template("param.html",info_message=session['info_message'],freq_min=session["freq_min"],freq_max=session["freq_max"],freq_show=session["freq_show"],acq_time=session["acq_time"],decay=session["decay"],phase=session["phase"],noise=session["noise"],time_delay=session["time_delay"],trace_every=session["trace_every"])

        elif "phase_info" in request.form:
            session['info_message']="""The phase of a resonance signal defines the starting point of its cosine function. A signal that has 0 radians phase starts at point (0,1) on the graph,
            and a signal with 0.5 pi radians phase starts at point (0,0) on the graph.<br><br>
            Not all protons in the sample have the same phase, because their phases depend on their chemical shifts.<br><br>
            In order to obtain a spectrum with a good baseline, the FID is usually "phase corrected" by adding or substracting phase angle from the signals.<br><br>
            For the sake of simplification, the present application allows you to visualize the effect of adding phase angle to all the protons in the same time, supposing that all of them have the same phase."""
            return render_template("param.html",info_message=session['info_message'],freq_min=session["freq_min"],freq_max=session["freq_max"],freq_show=session["freq_show"],acq_time=session["acq_time"],decay=session["decay"],phase=session["phase"],noise=session["noise"],time_delay=session["time_delay"],trace_every=session["trace_every"])

        elif "noise_info" in request.form:
            session['info_message']="""In actual NMR experiment, there is always a background noise in the FID.<br><br>This noise comes essentially from the electronics from which the spectrometer is made.<br><br>
            In order to reduce the noise, the FID is usually multiplied by "window functions" that reduce the effects of the noise on the final spectrum.<br><br>
            These window functions are not treated by the present application."""
            return render_template("param.html",info_message=session['info_message'],freq_min=session["freq_min"],freq_max=session["freq_max"],freq_show=session["freq_show"],acq_time=session["acq_time"],decay=session["decay"],phase=session["phase"],noise=session["noise"],time_delay=session["time_delay"],trace_every=session["trace_every"])

        elif "trace_every_info" in request.form:
            session['info_message']="""This parameter defines how many snapshots there will be in your final FT animation.<br><br>
            A small value gives a smoother animation, but the loading time will be longer."""
            return render_template("param.html",info_message=session['info_message'],freq_min=session["freq_min"],freq_max=session["freq_max"],freq_show=session["freq_show"],acq_time=session["acq_time"],decay=session["decay"],phase=session["phase"],noise=session["noise"],time_delay=session["time_delay"],trace_every=session["trace_every"])

        elif "about" in request.form:
            return render_template("about.html")


app.run()
