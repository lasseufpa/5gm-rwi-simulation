from Cheetah.Template import Template
import template_route as tpl
import base

if __name__ == '__main__':

    dia = [0.11,0.16,0.16,0.11,0.16,0.16,0.11,0.16,0.16,0.11,0.16,0.16]
    noite = [0.016,0.03,0.03,0.016,0.016,0.016,0.016,0.016,0.016,0.016,0.03,0.03]
    intermed = [0.022,0.042,0.042,0.022,0.042,0.042,0.022,0.042,0.042,0.022,0.032,0.032]

    # primeiro BEGIN = 100
    # primeiro END = 
    # probablity eh vetor e 
    t = ''
    ak_duration = 100

    actual_step = 10
    next_step = actual_step + ak_duration
    range_ptr = 0
    for episodios in range(2000):

        # DIA
        ran = [i+range_ptr for i in range(12)]
        dict_ = {'flow':ran,'probability':dia,'begin':str(actual_step),'end':str(next_step)}
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
        next_step = actual_step + ak_duration/4
        ran = [i+range_ptr for i in range(12)]
        dict_ = {'flow':ran,'probability':noite,'begin':str(actual_step),'end':str(next_step)}
        t += str(tpl.template_route(searchList=[dict_]))
        range_ptr += 12

        # INTERMED
        actual_step = next_step
        next_step = actual_step + ak_duration
        #ran = [i+range_ptr for i in range(12)]
        #dict_ = {'flow':ran,'probability':intermed,'begin':str(actual_step),'end':str(next_step)}
        #t += str(tpl.template_route(searchList=[dict_]))
        #range_ptr += 12

        actual_step = next_step
        next_step = actual_step + ak_duration

    #print(t)
    t2 = base.base(searchList=[{'XMLZAO_DA_PORRA':t}])
    print(t2)
