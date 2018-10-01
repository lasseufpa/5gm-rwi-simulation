from Cheetah.Template import Template
import template_route as tpl
import base

if __name__ == '__main__':

    dia = [0.11,0.16,0.16,0.11,0.16,0.16,0.11,0.16,0.16,0.11,0.16,0.16]
    noite = [0.016,0.03,0.03,0.016,0.016,0.016,0.016,0.016,0.016,0.016,0.03,0.03]
    intermed = [0.022,0.042,0.042,0.022,0.042,0.042,0.022,0.042,0.042,0.022,0.032,0.032]
    silence = [0.00016,0.0003,0.0003,0.00016,0.00016,0.00016,0.00016,0.00016,0.00016,0.00016,0.0003,0.0003]
    radical = [0.41,0.46,0.46,0.41,0.46,0.46,0.41,0.46,0.46,0.41,0.46,0.46]

    # primeiro BEGIN = 100
    # primeiro END = 
    # probablity eh vetor e
    t = ''
    ak_duration = 5 #duration of each stage

    actual_step = 10  #AK: I think it's the starting time
    next_step = actual_step + ak_duration
    range_ptr = 0
    for episodios in range(2000):

        # DIA
        #AK: I think the 12 magic number is because there are 12 flows
        ran = [i+range_ptr for i in range(12)]
        dict_ = {'flow':ran,'probability':radical,'begin':str(actual_step),'end':str(next_step)}
        #dict_ = {'flow':ran,'probability':intermed,'begin':str(actual_step),'end':str(next_step)}
        t += str(tpl.template_route(searchList=[dict_]))
        range_ptr += 12

        # INTERMED
      #  ran = [i+range_ptr for i in range(12)]
        #actual_step = next_step
        #next_step = actual_step + ak_duration
       # dict_ = {'flow':ran,'probability':intermed,'begin':str(actual_step),'end':str(next_step)}
       # t += str(tpl.template_route(searchList=[dict_]))
       # range_ptr += 12

        # NOITE
        actual_step = next_step
        next_step = actual_step + 17*ak_duration
        ran = [i+range_ptr for i in range(12)]
        dict_ = {'flow':ran,'probability':silence,'begin':str(actual_step),'end':str(next_step)}
        t += str(tpl.template_route(searchList=[dict_]))
        range_ptr += 12

        # INTERMED
        if 0:
            #enable stage with some
            actual_step = next_step
            next_step = actual_step + ak_duration
            ran = [i+range_ptr for i in range(12)]
            dict_ = {'flow':ran,'probability':intermed,'begin':str(actual_step),'end':str(next_step)}
            t += str(tpl.template_route(searchList=[dict_]))
            range_ptr += 12
        else:
            #use complete "silence", no traffic
            actual_step = next_step
            next_step = actual_step + 2*ak_duration

    #print(t)
    t2 = base.base(searchList=[{'XMLZAO_DA_PORRA':t}])
    print(t2)
