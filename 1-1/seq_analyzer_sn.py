# -*- coding: utf-8 -*-
"""seq_analyzer_sn.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ROUybA9xcDIgUZlPdGMFRI1XRoLVcjdZ
"""

"""Sequence analyzer."""

import numpy as np
import os
import copy
import matplotlib.pylab as plt
import scipy.signal

TrID = ["1.0","0.5","0.2"]
D  = ["100","10","1","01","6","06"]
Pe = ["0.06","0.60","6.00","60.0","1.00","10.0"]
rewID = ['"Displacement"','"FDifference"','"FAccumulated"']
alpha = [1.0,0.5,0.1]
gamma = [0.999,0.990,0.950,0.900,0.700,0.100]

tfdata = 100
file_txt = open("data-grad1-1-steps%d.txt" %(tfdata),'w')
file_txt.write("TrID,Pe,rewID,alpha,gamma,learned\n")

for R in range(len(rewID)):
   for T in range(len(TrID)):
      for P in range(len(Pe)):
      
         # Global parameters

         dir_   = './NoHLR-rand1.0-D%s-arp%s-gam0999-01/' %(D[P],TrID[T])

         nballs = 3
         nlinks = nballs-1

         #max_eps = 1
         #min_eps = 1
         #lambd = 0.01
         #total_reward = 0.0
         dt = 0.1

         alp = 0.60  #.65#.75
         lmax = 10. #1 #25
         lmin = (1-alp)*lmax

         # Load reward data
         eqlfile = 'evolqlquantities.txt'
         EQL = np.loadtxt(dir_+'/'+eqlfile)
         print(len(EQL))

         #tfdata = 500 #len(EQL)
         nqlsteps = tfdata-1 #tfdata-1

         """Extracting data from experience history.

         """

         rcase = R
         rw = [1,1,1]
         s_batch  = np.asarray(EQL[:tfdata,0],dtype=np.int32)
         a_batch  = np.asarray(EQL[:tfdata,1],dtype=np.int32)
         sn_batch = np.asarray(EQL[:tfdata,2],dtype=np.int32)
         #an_batch = np.asarray(EQL[1:tfdata,1],dtype=np.int32)

         z_batch  = s_batch #np.column_stack([s_batch[:-1],s_batch[1:]])
         zn_batch = sn_batch #np.column_stack([s_batch[1:],sn_batch[1:]])

         if   rcase == 0: # displacement
           r_batch = EQL[0:tfdata,3]
         elif rcase == 1: # flux diffence in one action
           r_batch = (EQL[0:tfdata,4]+EQL[0:tfdata,5]+EQL[0:tfdata,6]) - (EQL[0:tfdata,10]+EQL[0:tfdata,11]+EQL[0:tfdata,12])
         elif rcase == 2: # accumulated
           r_batch = (rw[0]*EQL[0:tfdata,7]+rw[1]*EQL[0:tfdata,8]+rw[2]*EQL[0:tfdata,9])*dt - 0.5*dt*(rw[0]*EQL[0:tfdata,4]+rw[1]*EQL[0:tfdata,5]+rw[2]*EQL[0:tfdata,6]+rw[0]*EQL[0:tfdata,10]+rw[1]*EQL[0:tfdata,11]+rw[2]*EQL[0:tfdata,12])
         elif rcase == 3: #
           r_batch = (rw[0]*EQL[0:tfdata,7]+rw[1]*EQL[0:tfdata,8]+rw[2]*EQL[0:tfdata,9])
         elif rcase == 4: #
           r_batch = (rw[0]*EQL[0:tfdata,7]+rw[1]*EQL[0:tfdata,8]+rw[2]*EQL[0:tfdata,9])*dt - 0.5*dt*(rw[0]*EQL[0:tfdata,4]+rw[1]*EQL[0:tfdata,5]+rw[2]*EQL[0:tfdata,6]+rw[0]*EQL[0:tfdata,10]+rw[1]*EQL[0:tfdata,11]+rw[2]*EQL[0:tfdata,12]) - (EQL[0:tfdata,4]+EQL[0:tfdata,5]+EQL[0:tfdata,6])
         else:            # at the end of action
           r_batch = (rw[0]*EQL[0:tfdata,4]+rw[1]*EQL[0:tfdata,5]+rw[2]*EQL[0:tfdata,6])*dt
         d_batch  = EQL[0:tfdata,3]

         """Plotting reward."""
         if False:
            data_sm = scipy.signal.savgol_filter(r_batch,1,0)
            fig, ax1 = plt.subplots()

            ax1.plot(data_sm)
            #plt.plot(r_batch)
            eqlfile = 'evoldofs.txt'
            EDOFS = np.loadtxt(dir_+'/'+eqlfile,skiprows=1)
            cm = (EDOFS[:10*tfdata,1]+EDOFS[:10*tfdata,7]+EDOFS[:10*tfdata,13])/3.

            color = 'tab:red'
            ax2 = ax1.twinx()
            #ax2.plot((cm[1:-1:10]-cm[0:-2:10]),color=color)
            ax2.plot(cm[0:-1:10],color=color)
            ax2.tick_params(axis='y',labelcolor=color)

            #plt.xlim([50,150])
            plt.grid()
            #plt.show()

         """Q-Learning from state $z_n$."""

         def QL_steps_zb(z_batch,zn_batch,a_batch,r_batch,alpha,gamma,replay_step):
           # Initilize QL matrix
           nstates = 2**nlinks
           nactions = nlinks

           MQL  = 0*1000 + np.zeros((nstates,nactions))
           MQLn = 0*1000 + np.zeros((nstates,nactions))
           DMQL = []

           # QL steps
           for it in range(nqlsteps):
             #print("\n##################################################")
             #print("\n    |-Time step #%5d" %(it))
             
             # Learning  #######################################################
             #prev_action_dec = a_batch[it]
             prev_state_dec  = z_batch[it]
             next_action_dec = a_batch[it]
             next_state_dec  = zn_batch[it]
             next_MQLmax     = np.max(MQL[next_state_dec,:])
             current_MQLval  = MQL[prev_state_dec,next_action_dec]
             current_reward  = r_batch[it]
             if False and prev_state_dec[0] == 3 and next_action_dec == 0:
               print(r_batch[it])

             MQL[prev_state_dec,next_action_dec] = (1-alpha)*current_MQLval + \
               alpha*(current_reward + gamma*next_MQLmax)

             DMQL.append(np.linalg.norm(MQL-MQLn))
             MQLn = copy.deepcopy(MQL)

             if it%replay_step == 0 and it > 0:
               MQL, DMQL = replay_zb(MQL,z_batch,zn_batch,a_batch,r_batch,alpha,gamma,DMQL)
               print('Replay done')

           return MQL, DMQL


         def replay_zb(MQL,z_batch,zn_batch,a_batch,r_batch,alpha,gamma,DMQL):
            #alpha = 1.0
            #gamma = 0.8
            nreplay = 2500 #50000
            MQLC = copy.deepcopy(MQL)
            MQLn = copy.deepcopy(MQL)
            #DQ = []
            for i in range(nreplay):     
               rl = np.random.randint(z_batch.shape[0], size=1)[0]
               prev_state_dec    = z_batch[rl]
               next_action_dec   = a_batch[rl]
               next_state_dec    = zn_batch[rl]
               next_MQLmax       = np.max(MQLC[next_state_dec,:])
               current_MQLval    = MQLC[prev_state_dec,next_action_dec]
               current_reward    = r_batch[rl]
               
               MQLC[prev_state_dec,next_action_dec] = (1-alpha)*current_MQLval + \
                  alpha*(current_reward + gamma*next_MQLmax)
                  
               DMQL.append(np.max(MQLC-MQLn)) #DMQL.append(np.linalg.norm(MQLC-MQLn))
               MQLn = copy.deepcopy(MQLC)
               #current_state_dec = next_state_dec
               #DQ.append([MQLC[0,0]-MQLC[0,1],MQLC[1,0]-MQLC[1,1],MQLC[2,0]-MQLC[2,1],MQLC[3,0]-MQLC[3,1]])
            
               
            return MQLC, DMQL  #, DQ#, next_state_dec


         def find_gait_zb(state_dec, MQL):
           #next_state_dec = copy.deepcopy(current_state_dec)
           slist = []
           alist = []
           current_state_dec = state_dec
           for j in range(10):
             action = np.zeros(nlinks, dtype=int)
             aux_current = np.array([int(i) for i in np.binary_repr(current_state_dec,width=nlinks)])
             action[np.argmax(MQL[current_state_dec,:])] = 1
             aux_state = np.remainder(aux_current+action,2*np.ones(nlinks, dtype=int))    
             next_state_dec = np.dot(aux_state,2**np.arange(nlinks-1,-1,-1,dtype=int))
             
             #print(current_state_dec, action)
             slist.append(current_state_dec)
             alist.append(action)
             
             current_state_dec = next_state_dec #copy.deepcopy(next_state_dec)

           return slist, alist

           
         def check_learned_policy(slist):
           slistend = slist[-4:]
           i0 = -1
           for i in range(4):
             if slistend[i] == 3:
               i0 = i
               break

           if i0 == -1:
             return 0

           i1 = (i0+1)%4
           i2 = (i1+1)%4
           i3 = (i2+1)%4

           if slistend[i1] == 1 and slistend[i2] == 0 and slistend[i3] == 2:
             return 1
           else:
             return 0

         gammalist = [0.999,0.99,0.95,0.9,0.7,0.1] #0.96
         alphalist = [1.0,0.5,0.1]

         replay_step = 10000*(nqlsteps-1)

         for alpha in alphalist:
           for gamma in gammalist:
             MQL, DMQL = QL_steps_zb(z_batch,zn_batch,a_batch,r_batch,alpha,gamma,replay_step)

             prev_state_dec  = z_batch[0]
             slist, alist = find_gait_zb(prev_state_dec, MQL)
             FDMQL = scipy.signal.savgol_filter(DMQL,15,0)
             #print(f'alpha = {alpha}, gamma = {gamma:.3f}, dQ = {FDMQL[-1]:e}, {slist}, {check_learned_policy(slist)}')
             
             file_txt.write(f"{TrID[T]},{Pe[P]},{rewID[R]},{alpha},{gamma:.3f},{check_learned_policy(slist)}\n")

             if False:
               plt.plot(DMQL)
               plt.plot(FDMQL)
               ax = plt.gca()
               ax.set_yscale('log')
      
      
      
      
file_txt.close()
